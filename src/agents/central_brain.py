"""
Looma agents — 中央大脑：意图解析 + 分发到内部能力端口

设计原则：不以占位为长期方案。中央大脑需结合 LLM 进化——意图解析、多轮理解、
编排与反思均可由 LLM 承担，通过改 Prompt 或模型即可迭代；规则仅作无 key 或
LLM 失败时的回退，保证链路可跑通。
来源：Tatha api/central_brain.py，已迁入 looma-zervi。
"""
from __future__ import annotations

import json
import random
import re
from typing import Any

from src.core.config import get_settings
from src.core.llm import get_llm

# 支持的意图（与 LLM 的 system prompt 一致，便于进化）
INTENTS = ("job_match", "resume_parse", "poetry", "credit", "mbti", "rag", "report", "unknown")

# 规则回退：关键词 → 意图（仅当 LLM 未启用或失败时使用）
INTENT_KEYWORDS = {
    "poetry": ["诗词", "诗人", "古诗", "推荐一句", "陪伴", "安慰", "思乡", "送别", "山水", "边塞", "励志", "一句诗"],
    "job_match": ["匹配", "职位", "找工作", "有没有适合", "岗位"],
    "resume_parse": ["上传", "简历", "解析简历"],
    "credit": ["征信", "信用", "验证"],
    "mbti": ["人格", "MBTI", "测评", "性格"],
    "report": ["报告", "日报", "周报", "月报", "统计"],
    "rag": ["知识库", "文档", "问一下", "查一下", "检索", "资料"],
}

# 诗词推荐时随机注入主题，避免「推荐一句诗」总返回同一首
POETRY_RECOMMEND_THEMES = ("思乡", "送别", "山水", "边塞", "咏物", "励志", "田园", "怀古")


def _poetry_is_recommendation_query(text: str) -> bool:
    """判断是否为「推荐一句诗」类短句（无诗词正文），以便注入随机主题。"""
    if not (text and text.strip()) or len(text.strip()) > 80:
        return False
    t = text.strip()
    return bool(re.search(r"推荐|来一句|来首|随便.*诗|一句诗", t))


def _parse_intent_llm(message: str) -> tuple[str, float, dict[str, Any]] | None:
    """
    用 LLM 解析意图（主路径）。返回 (intent, confidence, slots) 或 None（失败时回退）。
    """
    try:
        system = (
            "你是一个意图分类器。根据用户输入，输出且仅输出一个 JSON 对象，不要其他文字。"
            "JSON 必须包含：\"intent\"（取值仅限: job_match, resume_parse, poetry, credit, mbti, rag, report, unknown），"
            "\"confidence\"（0 到 1 的浮点数），可选 \"slots\"（对象，如 {\"query\": \"...\"}）。"
            "job_match=求职/职位匹配，resume_parse=上传或解析简历，poetry=诗词/诗人/陪伴，credit=征信/验证，"
            "mbti=人格测评，rag=知识库/文档问答，report=报告生成，unknown=其他。"
        )
        llm = get_llm()
        response = llm.complete(
            f"{system}\n\n用户输入：{message.strip() or '（无输入）'}\n\n请输出 JSON："
        )
        text = str(response).strip()
        # 允许被 markdown 代码块包裹
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if m:
                text = m.group(1).strip()
        data = json.loads(text)
        intent = (data.get("intent") or "unknown").lower()
        if intent not in INTENTS:
            intent = "unknown"
        confidence = float(data.get("confidence", 0.5))
        slots = data.get("slots") if isinstance(data.get("slots"), dict) else {}
        return (intent, confidence, slots)
    except Exception:
        return None


def _parse_intent_rules(message: str) -> str:
    """规则回退：关键词匹配。"""
    msg = (message or "").strip().lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return intent
    return "unknown"


def parse_intent(message: str) -> tuple[str, float, dict[str, Any]]:
    """
    解析用户消息得到意图 + 置信度 + 槽位。
    主路径：LLM（可进化）；回退：规则（保证无 key 时也能跑）。
    """
    # 尝试 LLM 解析
    out = _parse_intent_llm(message)
    if out is not None:
        return out
    # 回退规则
    intent = _parse_intent_rules(message)
    return (intent, 0.8 if intent != "unknown" else 0.3, {})


def dispatch(
    intent: str,
    query: str,
    context: dict[str, Any] | None = None,
    slots: dict[str, Any] | None = None,
    resume_text: str | None = None,
) -> dict[str, Any]:
    """
    按意图分发到内部能力端口，返回 result 字典。

    Args:
        intent: 解析出的意图
        query: 用户消息文本
        context: 可选上下文
        slots: LLM 解析出的槽位
        resume_text: 可选简历文本

    Returns:
        包含 message、status 等字段的 result dict
    """
    slots = slots or {}
    context = context or {}
    text = query.strip() or slots.get("text") or slots.get("content") or ""

    # ── RAG 问答 ──
    if intent == "rag":
        try:
            from src.retrieval.rag_engine import get_index
            index = get_index()
            query_engine = index.as_query_engine(similarity_top_k=3)
            response = query_engine.query(query)
            return {
                "message": "已检索知识库并生成回答",
                "status": "ok",
                "answer": str(response),
                "slots": slots,
            }
        except Exception as e:
            return {"message": "RAG 查询失败", "status": "error", "error": str(e), "slots": slots}

    # ── 职位匹配 ──
    if intent == "job_match":
        rtext = (
            (resume_text or "").strip()
            or (context or {}).get("resume_text") or ""
            or (slots.get("resume_text") or slots.get("resume") or "")
        )
        if not rtext:
            return {
                "message": "请先提供简历内容",
                "status": "pending",
                "hint": "可通过上传简历或在本请求中传入 resume_text",
                "slots": slots,
            }
        try:
            from src.pipeline.job_match_pipeline import run_job_match_pipeline
            results, total = run_job_match_pipeline(resume_text=rtext)
            return {
                "message": "已根据简历完成职位匹配",
                "status": "ok",
                "matches": results,
                "total_evaluated": total,
                "slots": slots,
            }
        except Exception as e:
            return {"message": "职位匹配失败", "status": "error", "error": str(e), "slots": slots}

    # ── 简历解析 ──
    if intent == "resume_parse":
        if text:
            try:
                from src.agents.document_agents import run_document_analysis
                extracted = run_document_analysis("resume", text)
                if extracted is not None:
                    return {"message": "已解析简历结构化信息", "status": "ok", "extracted": extracted.model_dump(), "slots": slots}
                return {"message": "简历解析未返回结果", "status": "pending", "hint": "请检查 API Key 与 LLM_MODEL", "slots": slots}
            except Exception as e:
                return {"message": "简历解析失败", "status": "error", "error": str(e), "slots": slots}
        return {"message": "简历上传与解析服务", "status": "pending", "hint": "请提供简历文本内容", "slots": slots}

    # ── 诗词推荐 ──
    if intent == "poetry":
        if text:
            try:
                from src.agents.poetry_search import search_poems
                search_query = text
                if _poetry_is_recommendation_query(text):
                    theme = random.choice(POETRY_RECOMMEND_THEMES)
                    search_query = theme

                poems = search_poems(search_query, n_results=3)
                if poems:
                    context_text = "\n\n".join(
                        f"【{p.get('dynasty', '')}】{p.get('title', '')} — {p.get('author', '')}\n{p.get('content', '')}"
                        for p in poems
                    )
                    prompt = (
                        f"从以下诗词中挑选最合适的一首推荐给用户。用户查询：{text}\n\n"
                        f"候选诗词：\n{context_text}\n\n"
                        f"请以 JSON 格式返回：title（标题）、author（作者）、dynasty（朝代）、"
                        f"content（选其中最有代表性的两句）、theme（主题如思乡/送别/励志等）。只输出 JSON。"
                    )
                    try:
                        llm = get_llm()
                        response = llm.complete(prompt)
                        resp_text = str(response).strip()
                        if "```" in resp_text:
                            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", resp_text)
                            if m:
                                resp_text = m.group(1).strip()
                        extracted = json.loads(resp_text)
                        return {"message": "已为您推荐诗词", "status": "ok", "extracted": extracted, "slots": slots}
                    except Exception:
                        best = poems[0]
                        return {
                            "message": "已为您检索诗词",
                            "status": "ok",
                            "extracted": {
                                "title": best.get("title", ""),
                                "author": best.get("author", ""),
                                "dynasty": best.get("dynasty", ""),
                                "content": (best.get("content", "") or "")[:100],
                                "theme": search_query,
                            },
                            "slots": slots,
                        }
                return {"message": "未找到匹配的诗词", "status": "pending", "hint": "请尝试其他主题词", "slots": slots}
            except Exception as e:
                return {"message": "诗词检索失败", "status": "error", "error": str(e), "slots": slots}
        return {"message": "诗人/诗词推荐已就绪", "status": "pending", "hint": "请描述您想找的诗词主题，如「推荐一句思乡的诗」", "slots": slots}

    # ── 征信分析 ──
    if intent == "credit":
        if text and len(text.strip()) >= 25:
            try:
                from src.agents.document_agents import run_document_analysis
                extracted = run_document_analysis("credit", text)
                if extracted is not None:
                    return {"message": "已解析征信相关信息", "status": "ok", "extracted": extracted.model_dump(), "slots": slots}
                return {"message": "征信解析未返回结果", "status": "pending", "hint": "请检查 API Key", "slots": slots}
            except Exception as e:
                return {"message": "征信解析失败", "status": "error", "error": str(e), "slots": slots}
        return {"message": "征信/验证服务", "status": "pending", "hint": "请提供信用报告摘要或主体文本", "slots": slots}

    # ── MBTI 测评 ──
    if intent == "mbti":
        from src.agents.mbti_analyzer import MBTITextAnalyzer, MIN_TEXT_LENGTH
        from src.agents.mbti_career_match import get_career_match

        if text and len(text.strip()) >= MIN_TEXT_LENGTH:
            try:
                analyzer = MBTITextAnalyzer()
                analysis = analyzer.analyze_text(text)
                if analysis.get("mbti_type") and analysis["mbti_type"] != "XXXX":
                    career = get_career_match(analysis["mbti_type"])
                    extracted = {**analysis, "career_match": career}
                    return {
                        "message": "已根据您的描述完成性格分析并给出职业建议",
                        "status": "ok",
                        "extracted": extracted,
                        "slots": slots,
                    }
                return {
                    "message": "已分析性格维度，建议补充更多描述以获得更稳定类型",
                    "status": "ok",
                    "extracted": analysis,
                    "slots": slots,
                }
            except Exception as e:
                return {"message": "人格测评分析失败", "status": "error", "error": str(e), "slots": slots}
        return {
            "message": "职业人格测评已就绪",
            "status": "pending",
            "hint": "请描述您的做事风格或发一段自述（至少20字），我会帮您分析性格类型并给出职业建议",
            "slots": slots,
        }

    # ── 报告生成 ──
    if intent == "report":
        try:
            from src.pipeline.report_gen import ReportGenerator
            reporter = ReportGenerator()
            # 从 query/slots 推断报告类型
            report_type = slots.get("report_type") or "daily"
            if "周" in query or "weekly" in query.lower():
                report_type = "weekly"
            elif "月" in query or "monthly" in query.lower():
                report_type = "monthly"

            if report_type == "daily":
                path = reporter.generate_daily()
            elif report_type == "weekly":
                path = reporter.generate_weekly()
            else:
                path = reporter.generate_monthly()

            return {"message": f"已生成{report_type}报告", "status": "ok", "path": str(path), "slots": slots}
        except Exception as e:
            return {"message": "报告生成失败", "status": "error", "error": str(e), "slots": slots}

    # ── 未知意图 ──
    return {"message": "暂未识别到明确意图", "status": "unknown", "received": (query or "")[:100]}