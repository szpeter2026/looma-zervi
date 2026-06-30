"""
Central Brain — Intent parsing + dispatch to internal capability ports.

Migrated from old central_brain.py (518 lines), adapted for Flask.
Design: rules-first (fast & reliable for 1.5B models), LLM as enhancement fallback.
"""
from __future__ import annotations
from __future__ import annotations

import json
import random
import re
import time
import logging
from typing import Any

import requests
from flask import current_app

logger = logging.getLogger("looma.brain")

INTENTS = ("job_match", "resume_parse", "poetry", "credit", "mbti", "rag", "report", "unknown")

# Keyword → intent rules (fallback when LLM unavailable)
INTENT_KEYWORDS = {
    "poetry": ["诗词", "诗人", "古诗", "推荐一句", "陪伴", "安慰", "思乡", "送别", "山水", "边塞", "励志", "一句诗", "唐诗", "宋词", "的诗", "的诗句", "词", "诗句", "绝句", "律诗"],
    "job_match": ["匹配", "职位", "找工作", "有没有适合", "岗位", "求职", "招聘"],
    "resume_parse": ["上传", "简历", "解析简历"],
    "credit": ["征信", "信用", "验证"],
    "mbti": ["人格", "MBTI", "测评", "性格"],
    "report": ["报告", "日报", "周报", "月报", "生成报告"],
    "rag": ["知识库", "文档", "问一下", "查一下", "检索", "资料", "总结", "介绍一下", "是什么", "什么是", "有哪些", "主要内容", "底座", "架构"],
}

POETRY_RECOMMEND_THEMES = ("思乡", "送别", "山水", "边塞", "咏物", "励志", "田园", "怀古")


def _poetry_is_recommendation_query(text: str) -> bool:
    """Check if query is a short 'recommend a poem' type (no poem content)."""
    if not (text and text.strip()) or len(text.strip()) > 80:
        return False
    t = text.strip()
    return bool(re.search(r"推荐|来一句|来首|随便.*诗|一句诗", t))


def _call_llm(prompt: str) -> str | None:
    """Call the configured LLM provider via DeepSeek/OpenAI API.
    Returns response text or None on failure."""
    config = current_app.config
    provider_order = [p.strip().lower() for p in config.get("LLM_PROVIDER_ORDER", "deepseek").split(",")]

    for provider in provider_order:
        try:
            if provider == "deepseek":
                url = f"{config['DEEPSEEK_BASE_URL']}/chat/completions"
                headers = {"Authorization": f"Bearer {config['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"}
                payload = {"model": config["DEEPSEEK_MODEL"], "messages": [{"role": "user", "content": prompt}], "temperature": 0.3}
                resp = requests.post(url, json=payload, headers=headers, timeout=float(config.get("API_REQUEST_TIMEOUT", 90)))
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

            elif provider == "openai":
                if not config.get("OPENAI_API_KEY"):
                    continue
                url = f"{config.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')}/chat/completions"
                headers = {"Authorization": f"Bearer {config['OPENAI_API_KEY']}", "Content-Type": "application/json"}
                payload = {"model": config.get("OPENAI_MODEL", "gpt-3.5-turbo"), "messages": [{"role": "user", "content": prompt}], "temperature": 0.3}
                resp = requests.post(url, json=payload, headers=headers, timeout=float(config.get("API_REQUEST_TIMEOUT", 90)))
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

            elif provider == "ollama":
                host = config.get("OLLAMA_HOST", "http://127.0.0.1:11434")
                url = f"{host.rstrip('/')}/api/generate"
                model = config.get("OLLAMA_MODEL", "qwen2.5-coder:1.5b")
                payload = {"model": model, "prompt": prompt, "stream": False}
                resp = requests.post(url, json=payload, timeout=float(config.get("API_REQUEST_TIMEOUT", 90)))
                resp.raise_for_status()
                return resp.json().get("response", "")

        except Exception as e:
            logger.warning(f"LLM provider {provider} failed: {e}")
            continue

    logger.error("All LLM providers unavailable")
    return None


def _parse_intent_llm(message: str) -> tuple[str, float, dict[str, Any]] | None:
    """Use LLM to parse intent. Returns (intent, confidence, slots) or None."""
    try:
        system = (
            "你是一个意图分类器。根据用户输入，输出且仅输出一个 JSON 对象，不要其他文字。"
            "JSON 必须包含：\"intent\"（取值仅限: job_match, resume_parse, poetry, credit, mbti, rag, report, unknown），"
            "\"confidence\"（0 到 1 的浮点数），可选 \"slots\"（对象）。"
            "\n分类规则："
            "\n- rag: 问知识/文档/概念/系统是什么、总结/介绍/检索"
            "\n- poetry: 涉及诗词/诗人/古诗/唐诗宋词"
            "\n- job_match: 求职/职位匹配/找工作"
            "\n- resume_parse: 上传或解析简历"
            "\n- credit: 征信/信用验证"
            "\n- mbti: 人格测评/MBTI/性格分析"
            "\n- report: 生成日报/周报/月报"
            "\n- unknown: 以上都不匹配"
        )
        response = _call_llm(f"{system}\n\n用户输入：{message.strip()}\n\n请输出 JSON：")
        if not response:
            return None

        text = response.strip()
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
    """Rules-based intent parsing (fast, reliable fallback)."""
    msg = (message or "").strip().lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return intent
    return "unknown"


def parse_intent(message: str, navigator_mode: bool = False) -> tuple[str, float, dict[str, Any]]:
    """Parse user message → intent + confidence + slots.
    Strategy: rules first (reliable), LLM as enhancement."""
    if navigator_mode:
        return ("unknown", 0.5, {})

    rule_intent = _parse_intent_rules(message)
    if rule_intent != "unknown":
        return (rule_intent, 0.9, {})

    out = _parse_intent_llm(message)
    if out is not None:
        intent, confidence, slots = out
        if intent != "unknown" and confidence >= 0.7:
            return (intent, confidence, slots)

    return ("unknown", 0.3, {})


def dispatch(
    intent: str,
    query: str,
    context: dict[str, Any] | None = None,
    slots: dict[str, Any] | None = None,
    resume_text: str | None = None,
    _timing: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Dispatch intent → internal capability port, return result dict."""
    slots = slots or {}
    context = context or {}
    text = query.strip() or slots.get("text") or slots.get("content") or ""
    _timing = _timing or {}

    # ── RAG 问答 ──
    if intent == "rag":
        try:
            from src.rag.chroma_client import search_chroma
            t_retrieve = time.time()
            results = search_chroma(query, n_results=3)
            _timing["rag_retrieve"] = int((time.time() - t_retrieve) * 1000)

            context_text = "\n\n".join(r.get("content", "") for r in results) if results else "(no context)"

            t_llm = time.time()
            prompt = (
                "你是一个知识库助手。根据以下参考资料回答用户问题。"
                "如果参考资料不足以回答问题，请如实说明。\n\n"
                f"参考资料：\n{context_text}\n\n"
                f"用户问题：{query}\n\n"
                f"回答："
            )
            answer = _call_llm(prompt) or "知识库检索失败，请稍后再试"
            _timing["rag_llm"] = int((time.time() - t_llm) * 1000)

            sources = [{"chunk_text": r.get("content", "")[:200], "score": r.get("score")} for r in results]
            return {"answer": answer, "_sources": sources, "slots": slots}
        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            return {"message": f"RAG 查询失败: {str(e)}", "answer": "", "slots": slots}

    # ── 职位匹配 ──
    if intent == "job_match":
        rtext = (resume_text or "").strip() or (context.get("resume_text") or "") or (slots.get("resume_text") or "")
        if not rtext:
            return {"message": "请先提供简历内容", "status": "pending",
                    "hint": "可通过上传简历或传入 resume_text", "slots": slots}
        try:
            from src.pipeline.job_match_pipeline import run_job_match_pipeline
            results_list, total = run_job_match_pipeline(resume_text=rtext)
            return {"message": "已根据简历完成职位匹配", "matches": results_list, "total_evaluated": total, "slots": slots}
        except Exception as e:
            return {"message": "职位匹配失败", "error": str(e), "slots": slots}

    # ── 简历解析 ──
    if intent == "resume_parse":
        if text:
            try:
                from src.agents.document_agents import run_document_analysis
                extracted = run_document_analysis("resume", text)
                return {"message": "已解析简历", "extracted": extracted, "slots": slots}
            except Exception as e:
                return {"message": "简历解析失败", "error": str(e), "slots": slots}
        return {"message": "请提供简历文本内容", "status": "pending", "slots": slots}

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
                        f"请以 JSON 格式返回：title、author、dynasty、content（选最有代表性的两句）、theme。只输出 JSON。"
                    )
                    response = _call_llm(prompt)
                    if response:
                        resp_text = response.strip()
                        if "```" in resp_text:
                            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", resp_text)
                            if m:
                                resp_text = m.group(1).strip()
                        try:
                            extracted = json.loads(resp_text)
                            if isinstance(extracted.get("content"), list):
                                extracted["content"] = "\n".join(extracted["content"])
                            return {"message": "已为您推荐诗词", "extracted": extracted, "slots": slots}
                        except json.JSONDecodeError:
                            pass

                    # LLM failed, return first poem from search
                    best = poems[0]
                    return {
                        "extracted": {
                            "title": best.get("title", ""), "author": best.get("author", ""),
                            "dynasty": best.get("dynasty", ""),
                            "content": (best.get("content", "") or "")[:100],
                            "theme": search_query,
                        },
                        "slots": slots,
                    }
                return {"message": "未找到匹配的诗词", "status": "pending", "slots": slots}
            except Exception as e:
                return {"message": "诗词检索失败", "error": str(e), "slots": slots}
        return {"message": "诗人/诗词推荐已就绪", "status": "pending", "slots": slots}

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
                    return {"extracted": {**analysis, "career_match": career}, "slots": slots}
                return {"extracted": analysis, "slots": slots}
            except Exception as e:
                return {"message": "人格测评分析失败", "error": str(e), "slots": slots}
        return {"message": "请描述您的做事风格（至少20字）", "status": "pending", "slots": slots}

    # ── 报告生成 ──
    if intent == "report":
        try:
            from src.pipeline.report_gen import ReportGenerator
            reporter = ReportGenerator()
            report_type = "daily"
            if "周" in query or "weekly" in query.lower():
                report_type = "weekly"
            elif "月" in query or "monthly" in query.lower():
                report_type = "monthly"
            path = reporter.generate_report(report_type)
            return {"message": f"已生成{report_type}报告", "path": str(path), "slots": slots}
        except Exception as e:
            return {"message": "报告生成失败", "error": str(e), "slots": slots}

    # ── Navigator 对话模式 ──
    if context.get("navigator_mode") and intent == "unknown":
        try:
            user_id = context.get("user_id", "guest")
            session_id = context.get("session_id", "")
            session_history = context.get("session_history", [])
            current_stage = context.get("current_stage", "greeting")
            active_domain = context.get("active_domain", "")
            session_num = context.get("session_num", 1)
            interaction_count = context.get("interaction_count", 0)

            # ── Engine initialization ──
            db = current_app._db if hasattr(current_app, '_db') else None
            from src.agents.domain_engine import get_domain_engine
            from src.agents.navigator_memory import get_navigator_memory
            from src.agents.convergence import get_convergence

            engine = get_domain_engine(db=db)
            memory = get_navigator_memory(db=db)
            convergence = get_convergence(engine=engine, memory=memory)

            # ── Stage: domain_enter → record domain entry + cross-domain effects ──
            domain_context: dict = {}
            if current_stage == "domain_enter" and active_domain:
                crossing = engine.record_domain_enter(user_id, session_id, active_domain)
                if crossing:
                    domain_context = crossing

            # ── Stage: choice_made → record choice + imprint ──
            if current_stage == "choice_made" and active_domain:
                user_choice = context.get("last_choice", "")
                if user_choice:
                    engine.record_choice(session_id, active_domain, user_choice, user_id)
                    importance = context.get("choice_importance", 1.0)
                    memory.record_choice(user_id, active_domain, user_choice,
                                         importance=importance, session_id=session_id)

            # ── Intelligence: detect emergent strategies ──
            strategies = engine.detect_strategies(user_id)
            if strategies and db:
                for s in strategies:
                    try:
                        db.log_emergent_strategy(user_id, s["strategy"])
                    except Exception:
                        pass

            # ── Check convergence trigger ──
            if convergence.should_trigger_convergence(user_id, session_id, interaction_count):
                current_stage = "convergence"
                convergence.mark_convergence_triggered(session_id)
                logger.info(f"Convergence triggered: user={user_id} session={session_id}")

            # ── Build Navigator system prompt (core of the engine) ──
            navigator_system = convergence.build_system_prompt(
                user_id=user_id,
                session_id=session_id,
                active_domain=active_domain or None,
                confidence=context.get("confidence", 0.5),
                stage=current_stage,
                query=query,
                session_num=session_num,
            )

            # ── Psychology layer (optional enhancement) ──
            psychology_hint = ""
            if current_app.config.get("PSYCHOLOGY_ENABLED", True):
                try:
                    from src.agents.psychology_analyzer import analyze_conversation, build_psychology_hint
                    psychology_result = analyze_conversation(query, session_history, active_domain)
                    psychology_hint = build_psychology_hint(psychology_result)
                except Exception:
                    pass

            # ── Build chat history ──
            history_text = ""
            for msg in session_history[-4:]:
                role = "用户" if msg.get("role") == "user" else "Navigator"
                content = msg.get("content", "")[:80]
                history_text += f"{role}：{content}\n"

            # ── Assemble full prompt ──
            domain_hint = f"[当前域：{active_domain}]\n" if active_domain else ""

            # Inject domain crossing narrative if available
            crossing_narrative = ""
            if domain_context.get("crossing_narrative"):
                crossing_narrative = f"\n[跨域感知 — 注入你的回应中]\n{domain_context['crossing_narrative']}\n"

            # Inject echo narrative if active
            echo_narrative = ""
            if domain_context.get("echo") and domain_context["echo"].get("narrative_hint"):
                echo_narrative = f"\n[回声感知 — 你感知到跨域共鸣]\n{domain_context['echo']['narrative_hint']}\n"

            full_prompt = (
                f"{navigator_system}\n\n"
                f"{domain_hint}"
                f"{psychology_hint}\n"
                f"{crossing_narrative}"
                f"{echo_narrative}"
                f"[对话历史]\n{history_text}\n"
                f"[用户消息] {query}\n\n"
                f"请以 Navigator 身份回应（不超过120字，纯文本）："
            )

            t_nav = time.time()
            answer = _call_llm(full_prompt) or "...（信号中断）"
            _timing["navigator_llm"] = int((time.time() - t_nav) * 1000)

            # Build engine metadata for response
            engine_ctx = engine.build_navigator_context(user_id, session_id)
            navigator_extras: dict = {
                "navigator_mode": True,
                "current_stage": current_stage,
                "active_domain": active_domain,
                "estimated_act": engine_ctx.get("estimated_act"),
                "imprint": engine_ctx.get("imprint"),
                "echo_chain": engine_ctx.get("echo_chain_length", 0),
                "convergence_triggered": current_stage == "convergence",
                "active_strategies": engine_ctx.get("active_strategies", []),
                "domain_context": domain_context,
            }
            # Remove null-ish values
            navigator_extras = {k: v for k, v in navigator_extras.items() if v not in (None, "", [], {})}

            return {
                "answer": answer.strip(),
                "extracted": navigator_extras,
                "slots": slots,
            }
        except Exception as e:
            logger.error(f"Navigator failed: {e}", exc_info=True)
            return {"answer": "...（信号中断）", "slots": slots}

    # ── Unknown ──
    return {"message": "暂未识别到明确意图", "answer": "", "received": (query or "")[:100]}
