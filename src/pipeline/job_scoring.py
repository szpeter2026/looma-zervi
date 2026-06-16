"""
Looma pipeline — 简历 vs 职位 LLM 打分

PydanticAI Agent，输入简历+职位描述，输出 JobMatchScore。
借鉴 DailyJobMatch / resume-optimization-crew 的多维度打分结构。
来源：Tatha jobs/scoring.py，已迁入 looma-zervi。
"""
from __future__ import annotations

from src.core.config import get_settings
from src.pipeline.job_schemas import JobMatchScore

_agent = None


def _job_match_agent():
    """
    创建 PydanticAI Agent，使用 LiteLLM + PydanticAI 输出结构化打分。
    若 pydantic_ai / pydantic_ai_litellm 未安装则静默返回 None。
    """
    try:
        from pydantic_ai import Agent
        from pydantic_ai_litellm import LiteLLMModel
    except ImportError:
        return None

    settings = get_settings()
    model = LiteLLMModel(model_name=settings.LLM_MODEL)
    return Agent(
        model=model,
        output_type=JobMatchScore,
        system_prompt=(
            "你是一个职位匹配评分员。根据「简历」与「职位描述」两段文本，从以下维度打分并只输出结构化结果。"
            "不要输出任何解释或前缀（如「好的」「这是」），只输出符合 JobMatchScore 的 JSON。\n"
            "维度与范围：\n"
            "- background_match: 领域/背景匹配 0–10\n"
            "- skills_overlap: 技能重叠 0–30\n"
            "- experience_relevance: 经历相关性 0–30\n"
            "- seniority: 职级匹配 0–10\n"
            "- language_requirement: 语言要求匹配 0–10\n"
            "- company_score: 公司/岗位吸引力 0–10\n"
            "- salary_match: 钱多——薪资/待遇与候选人期望或市场匹配 0–10，未提及则 5\n"
            "- location_match: 离家近——工作地点、远程/混合与候选人偏好匹配 0–10，未提及则 5\n"
            "- culture_workload_match: 事少——工作强度、弹性、加班文化、团队氛围匹配 0–10，未提及则 5\n"
            "- overall: 综合分 0–100，需综合考虑上述所有维度（含钱多、事少、离家近），为各项加权综合\n"
            "同时填写 summary（一句话匹配摘要，可提及薪资/地点/强度亮点）、keywords、fit_bullets（最多 5 条）。"
        ),
    )


def score_resume_vs_job(resume_text: str, job_description: str) -> JobMatchScore:
    """
    对单条职位做简历匹配打分。

    优先使用 PydanticAI Agent（结构化输出），若不可用则回退到 LiteLLM 直接调用。
    若 LLM 调用失败，返回 overall=0 的默认分。
    """
    global _agent
    if _agent is None:
        _agent = _job_match_agent()

    user_message = f"【简历】\n{resume_text[:8000]}\n\n【职位描述】\n{(job_description or '')[:4000]}"

    # 优先路径：PydanticAI Agent
    if _agent is not None:
        try:
            result = _agent.run_sync(user_message)
            return result.output
        except Exception as e:
            err_msg = (str(e).strip() or type(e).__name__)[:120]
            if "key" in err_msg.lower() or "secret" in err_msg.lower() or "auth" in err_msg.lower():
                err_msg = type(e).__name__ + "（请检查 .env 中对应 API Key 与 LLM_MODEL）"
            return JobMatchScore(
                overall=0,
                summary=f"打分失败: {err_msg}",
            )

    # 回退路径：通过 LiteLLM 直接调用
    try:
        from src.core.llm import get_llm
        llm = get_llm()
        response = llm.complete(
            f"{_agent_system_prompt()}\n\n{user_message}\n\n请以 JSON 格式输出匹配评分。"
        )
        import json, re
        text = str(response).strip()
        if "```" in text:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if m:
                text = m.group(1).strip()
        data = json.loads(text)
        return JobMatchScore(**data)
    except Exception as e:
        err_msg = (str(e).strip() or type(e).__name__)[:120]
        return JobMatchScore(
            overall=0,
            summary=f"打分失败: {err_msg}",
        )


def _agent_system_prompt() -> str:
    return (
        "你是一个职位匹配评分员。根据「简历」与「职位描述」两段文本，从以下维度打分：\n"
        "background_match(0-10), skills_overlap(0-30), experience_relevance(0-30), "
        "seniority(0-10), language_requirement(0-10), company_score(0-10), "
        "salary_match(0-10), location_match(0-10), culture_workload_match(0-10), "
        "overall(0-100, 综合加权)，summary（摘要），keywords（关键字列表），fit_bullets（匹配要点最多5条）。"
    )