"""
Job Match Pipeline — Match resumes to job listings with multi-dimension LLM scoring.

Migrated from Tatha's scoring engine.  Uses _call_llm() with structured prompts
for 11-dimension scoring (钱多事少离家近 + 技能/经验/职级/公司吸引力等).
"""
from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger("looma.job_match")


def _score_resume_vs_job(resume_text: str, job_info: dict) -> dict:
    """Score one resume against one job description via LLM.

    Returns a dict with multi-dimension scores matching Tatha's JobMatchScore schema.
    """
    from src.agents.central_brain import _call_llm

    title = job_info.get("title", "")
    company = job_info.get("company", "")
    location = job_info.get("location", "")
    description = job_info.get("description", "") or f"{title} @ {company}"
    salary_range = job_info.get("salary_range", "")

    # Build rich job description for scoring
    jd_parts = [description]
    if location:
        jd_parts.insert(0, f"工作地点：{location}")
    if salary_range:
        jd_parts.insert(0, f"薪资范围：{salary_range}")
    if company:
        jd_parts.insert(0, f"公司：{company}")
    if title:
        jd_parts.insert(0, f"职位：{title}")

    jd_text = "\n".join(jd_parts)

    prompt = (
        "你是一个职位匹配评分专家。根据「简历」与「职位描述」两段文本，从以下维度打分并只输出结构化 JSON 结果。"
        "不要输出任何解释或前缀（如「好的」「这是」），只输出符合格式的 JSON。\n\n"
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
        "- summary: 一句话匹配摘要（可提及薪资/地点/强度亮点，30字以内）\n"
        "- keywords: 匹配关键词列表（3-8个）\n"
        "- fit_bullets: 匹配要点列表（3-5条，每条15字以内）\n\n"
        "输出格式：\n"
        "{\n"
        '  "overall": 85,\n'
        '  "background_match": 8,\n'
        '  "skills_overlap": 25,\n'
        '  "experience_relevance": 25,\n'
        '  "seniority": 8,\n'
        '  "language_requirement": 8,\n'
        '  "company_score": 7,\n'
        '  "salary_match": 6,\n'
        '  "location_match": 7,\n'
        '  "culture_workload_match": 5,\n'
        '  "summary": "技能高度匹配，地点便利，薪资有竞争力",\n'
        '  "keywords": ["Python", "FastAPI", "NLP"],\n'
        '  "fit_bullets": ["技能高度重叠", "行业背景匹配", "地点便利"]\n'
        "}\n\n"
        f"【简历内容】\n{resume_text[:4000]}\n\n"
        f"【职位描述】\n{jd_text[:4000]}\n\n"
        "请输出 JSON："
    )

    try:
        response = _call_llm(prompt)
    except Exception as e:
        logger.warning(f"LLM call failed for job scoring: {e}")
        return _default_score()

    if not response:
        return _default_score()

    resp = response.strip()
    if "```" in resp:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", resp)
        if m:
            resp = m.group(1).strip()

    try:
        scores = json.loads(resp)
        return _sanitize_scores(scores)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON for job scoring, using defaults")
        return _default_score()


def _sanitize_scores(raw: dict) -> dict:
    """Clamp all score fields to valid ranges and fill in defaults."""
    def _clamp(val, lo, hi, default=None):
        try:
            v = int(float(val))
            return max(lo, min(hi, v))
        except (TypeError, ValueError):
            return default if default is not None else lo

    return {
        "overall":                _clamp(raw.get("overall"), 0, 100, 50),
        "background_match":        _clamp(raw.get("background_match"), 0, 10, 5),
        "skills_overlap":          _clamp(raw.get("skills_overlap"), 0, 30, 15),
        "experience_relevance":    _clamp(raw.get("experience_relevance"), 0, 30, 15),
        "seniority":               _clamp(raw.get("seniority"), 0, 10, 5),
        "language_requirement":    _clamp(raw.get("language_requirement"), 0, 10, 5),
        "company_score":           _clamp(raw.get("company_score"), 0, 10, 5),
        "salary_match":            _clamp(raw.get("salary_match"), 0, 10, 5),
        "location_match":          _clamp(raw.get("location_match"), 0, 10, 5),
        "culture_workload_match":  _clamp(raw.get("culture_workload_match"), 0, 10, 5),
        "summary":                 raw.get("summary", ""),
        "keywords":                raw.get("keywords") if isinstance(raw.get("keywords"), list) else [],
        "fit_bullets":             raw.get("fit_bullets") if isinstance(raw.get("fit_bullets"), list) else [],
    }


def _default_score() -> dict:
    """Fallback score when LLM fails."""
    return {
        "overall": 50,
        "background_match": 5,
        "skills_overlap": 15,
        "experience_relevance": 15,
        "seniority": 5,
        "language_requirement": 5,
        "company_score": 5,
        "salary_match": 5,
        "location_match": 5,
        "culture_workload_match": 5,
        "summary": "AI 评分暂不可用",
        "keywords": [],
        "fit_bullets": [],
    }


def word_overlap_score(resume_text: str, job_desc: str) -> int:
    """Simple keyword overlap score (0-100), used only as tiebreaker."""
    if not job_desc:
        return 0
    resume_words = set(resume_text.lower().split())
    job_words = set(job_desc.lower().split())
    if not job_words:
        return 0
    overlap = len(resume_words & job_words)
    ratio = min(1.0, overlap / len(job_words))
    return int(ratio * 100)


def run_job_match_pipeline(
    resume_text: str,
    jobs: list[dict] | None = None,
) -> tuple[list[dict], int]:
    """Score a resume against each job, sort by overall score, return top matches.

    Args:
        resume_text: Full resume content for matching
        jobs:        List of job dicts (id, title, company, location, salary_range, description).
                     If None, uses MOCK_JOPS from the old pipeline.

    Returns:
        (matches list, total evaluated count)
    """
    resume_text = (resume_text or "").strip()
    if not resume_text:
        return [], 0

    if jobs is None:
        from src.api.routes.jobs_routes import MOCK_JOBS
        jobs = MOCK_JOBS

    if not jobs:
        return [], 0

    results = []
    for job in jobs:
        score = _score_resume_vs_job(resume_text, job)

        # Build the match result combining job info + scores + derived display fields
        match = {
            "job_id": job.get("id", ""),
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "salary_range": job.get("salary_range", ""),
            # Multi-dimension scores (from Tatha's model)
            "scores": score,
            # Legacy display fields (backward compatible with frontend)
            "reason": score.get("summary", ""),
            "matched_skills": score.get("keywords", []),
            "missing_skills": [],
            "fit_bullets": score.get("fit_bullets", []),
        }
        results.append(match)

    # Sort by overall score descending
    results.sort(key=lambda m: m["scores"]["overall"], reverse=True)
    return results, len(results)
