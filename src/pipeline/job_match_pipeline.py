"""
Looma pipeline — 职位匹配流水线

拉取职位 → 逐条 LLM 打分 → 排序取 Top-N。
来源：Tatha jobs/pipeline.py，已迁入 looma-zervi。
"""
from __future__ import annotations

from src.core.config import get_settings
from src.pipeline.job_schemas import MatchResult
from src.pipeline.job_scoring import score_resume_vs_job

# 单次流水线最多对多少条职位做 LLM 打分（控制成本）
MAX_JOBS_TO_SCORE = 20

# Mock 职位数据（无外接 API 时使用）
MOCK_JOBS = [
    {
        "title": "Python 后端开发工程师",
        "company": "字节跳动",
        "location": "北京·海淀",
        "description": "负责后端服务开发与维护，使用 Python/FastAPI/Django，熟悉 PostgreSQL 和 Redis，有微服务经验优先。",
    },
    {
        "title": "全栈开发工程师",
        "company": "腾讯",
        "location": "深圳·南山",
        "description": "全栈开发，React + Node.js/Python 后端，参与产品从 0 到 1 搭建，有 AI 产品经验加分。",
    },
    {
        "title": "AI 算法工程师",
        "company": "阿里巴巴",
        "location": "杭州·余杭",
        "description": "大模型应用开发，熟悉 LangChain/LlamaIndex，有 RAG 系统设计经验，熟悉向量数据库。",
    },
    {
        "title": "数据分析师",
        "company": "美团",
        "location": "上海·长宁",
        "description": "业务数据分析，熟练使用 SQL/Python，有数据仓库经验，能独立完成分析报告。",
    },
    {
        "title": "前端开发工程师",
        "company": "百度",
        "location": "北京·上地",
        "description": "负责 Web 前端开发，使用 React/Vue，有 TypeScript 经验，了解 Node.js。",
    },
]


def _mock_job_source(limit: int = 10) -> list[dict]:
    """Mock 职位源：返回示例职位列表，无需 API Key。"""
    return MOCK_JOBS[:limit]


def _build_jd(job: dict) -> str:
    """拼接职位描述文本，含地点信息供「离家近」维度打分。"""
    jd = (job.get("description") or f"{job.get('title')} @ {job.get('company')}").strip()
    if job.get("location"):
        jd = f"工作地点：{job['location']}\n\n{jd}"
    return jd


def run_job_match_pipeline(
    resume_text: str,
    top_n: int = 5,
    source_id: str | None = None,
) -> tuple[list[dict], int]:
    """
    执行一次职位匹配：用职位源拉职位，对每条做简历 vs 职位描述打分，按 overall 排序后返回前 top_n 条。

    Args:
        resume_text: 简历全文文本
        top_n: 返回前 N 条匹配
        source_id: 职位源 ID（mock | apify_linkedin），不传则用 mock

    Returns:
        (匹配列表, 参与打分的职位数)
    """
    resume_text = (resume_text or "").strip()
    if not resume_text:
        return [], 0

    settings = get_settings()
    n = max(1, min(top_n, 20))

    # 获取职位源（当前仅 mock）
    if source_id == "apify_linkedin":
        import os
        apify_key = os.getenv("APIFY_API_KEY", "")
        if not apify_key:
            return [], 0
        # TODO: P2 接入 Apify LinkedIn Job Scraper
        return [], 0

    jobs = _mock_job_source(limit=MAX_JOBS_TO_SCORE)
    if not jobs:
        return [], 0

    results: list[dict] = []
    for job in jobs:
        jd = _build_jd(job)
        score = score_resume_vs_job(resume_text, jd)
        results.append({
            "job": {
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "description": job.get("description", ""),
            },
            "score": score.model_dump(),
        })

    results.sort(key=lambda r: r["score"].get("overall", 0), reverse=True)
    return results[:n], len(results)