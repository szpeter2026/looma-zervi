"""Looma api — 职位匹配路由"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.models import JobMatchRequest, JobMatchResponse, JobMatchItem, JobScores
from src.api.auth import AuthContext, get_auth
from src.api.quota import consume, clamp_top_n, RESOURCE_JOB_MATCH
from src.pipeline.job_match_pipeline import run_job_match_pipeline

router = APIRouter(tags=["jobs"])


@router.post("/v1/jobs/match", response_model=JobMatchResponse)
def jobs_match(request: JobMatchRequest, auth: AuthContext = Depends(get_auth)):
    """职位匹配流水线：简历 vs 职位打分 → 排序返回 Top-N"""
    if not consume(auth.user_id, auth.tier, RESOURCE_JOB_MATCH):
        raise HTTPException(status_code=429, detail={"code": "quota_exceeded", "message": "当日配额已用尽"})

    top_n = clamp_top_n(auth.tier, request.top_k or 5)
    try:
        results, total = run_job_match_pipeline(
            resume_text=request.resume_text,
            top_n=top_n,
        )
        matches = []
        for r in results:
            s = r["score"]
            matches.append(JobMatchItem(
                job_id=r.get("job_id", ""),
                title=r["job"]["title"],
                company=r["job"]["company"],
                location=r["job"].get("location", ""),
                salary_range=r["job"].get("salary_range"),
                scores=JobScores(
                    money=s.get("salary_match", 5),
                    workload=s.get("culture_workload_match", 5),
                    proximity=s.get("location_match", 5),
                    overall=s.get("overall", 0),
                ),
                reason=s.get("summary", ""),
            ))
        return JobMatchResponse(matches=matches, total_evaluated=total)
    except Exception as e:
        return JobMatchResponse(matches=[], total_evaluated=0)