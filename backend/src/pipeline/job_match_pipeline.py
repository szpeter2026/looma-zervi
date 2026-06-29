"""
Job Match Pipeline — Match resumes to job listings.
Migrated from old job_match_pipeline.py, adapted for Flask.
Uses LLM for scoring + ChromaDB for job data retrieval.
"""
from __future__ import annotations
import json
import logging
import re
from flask import current_app

logger = logging.getLogger("looma.job_match")

# Mock job data for MVP (real data comes from ChromaDB or DB later)
MOCK_JOBS = [
    {"job_id": "j1", "title": "前端开发工程师", "company": "字节跳动", "location": "深圳",
     "salary_range": "25-40K", "description": "负责抖音前端开发，React/Vue"},
    {"job_id": "j2", "title": "Python 后端开发", "company": "腾讯", "location": "深圳",
     "salary_range": "20-35K", "description": "微服务架构开发，FastAPI/Django"},
    {"job_id": "j3", "title": "AI 算法工程师", "company": "华为", "location": "深圳",
     "salary_range": "30-50K", "description": "NLP/推荐系统算法研发"},
    {"job_id": "j4", "title": "产品经理", "company": "阿里", "location": "杭州",
     "salary_range": "25-45K", "description": "电商产品规划与迭代"},
    {"job_id": "j5", "title": "数据分析师", "company": "美团", "location": "北京",
     "salary_range": "20-30K", "description": "业务数据分析与可视化"},
]


def run_job_match_pipeline(resume_text: str) -> tuple[list[dict], int]:
    """Run job matching pipeline on a resume text.

    Returns: (matches_list, total_evaluated)
    """
    if not resume_text:
        return [], 0

    # MVP: use LLM to score resume against mock jobs
    try:
        from src.agents.central_brain import _call_llm

        jobs_text = "\n".join(
            f"{j['job_id']}: {j['title']} @ {j['company']} ({j['location']}) {j['salary_range']} — {j['description']}"
            for j in MOCK_JOBS
        )

        prompt = (
            "你是职位匹配专家。根据简历内容，对以下职位进行评分。\n"
            "对每个职位输出 JSON 数组，每项包含：job_id, overall_score (0-100), "
            "reason (为什么匹配/不匹配)。\n\n"
            f"职位列表：\n{jobs_text}\n\n"
            f"简历内容：\n{resume_text[:2000]}\n\n"
            "只输出 JSON 数组："
        )

        response = _call_llm(prompt)
        if not response:
            return _fallback_match(resume_text), len(MOCK_JOBS)

        resp = response.strip()
        if "```" in resp:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", resp)
            if m:
                resp = m.group(1).strip()

        try:
            scores = json.loads(resp)
            if isinstance(scores, dict):
                scores = scores.get("matches", [scores])
        except json.JSONDecodeError:
            return _fallback_match(resume_text), len(MOCK_JOBS)

        # Build matches
        matches = []
        for s in scores:
            job_id = s.get("job_id", "")
            score = float(s.get("overall_score", 0))
            reason = s.get("reason", "")

            # Find matching mock job
            job = next((j for j in MOCK_JOBS if j["job_id"] == job_id), None)
            if job:
                matches.append({
                    "job_id": job_id,
                    "title": job["title"],
                    "company": job["company"],
                    "location": job["location"],
                    "salary_range": job["salary_range"],
                    "scores": {
                        "overall": score,
                        "money": score * 0.3,
                        "workload": score * 0.2,
                        "proximity": score * 0.5,
                    },
                    "reason": reason,
                })

        # Sort by overall score
        matches.sort(key=lambda m: m["scores"]["overall"], reverse=True)
        return matches, len(MOCK_JOBS)

    except Exception as e:
        logger.error(f"Job match pipeline failed: {e}")
        return _fallback_match(resume_text), len(MOCK_JOBS)


def _fallback_match(resume_text: str) -> list[dict]:
    """Simple keyword-based fallback matching."""
    text_lower = resume_text.lower()
    matches = []
    for job in MOCK_JOBS:
        desc_lower = job["description"].lower()
        overlap = sum(1 for word in desc_lower.split() if word in text_lower)
        score = min(100, overlap * 20)
        if score > 0:
            matches.append({
                "job_id": job["job_id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "salary_range": job["salary_range"],
                "scores": {"overall": score},
                "reason": f"关键词重叠度 {overlap}",
            })
    matches.sort(key=lambda m: m["scores"]["overall"], reverse=True)
    return matches
