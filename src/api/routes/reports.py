"""Looma api — 报告生成路由"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.models import ReportGenerateRequest, ReportMeta
from src.api.auth import AuthContext, get_auth
from src.pipeline.report_gen import ReportGenerator

router = APIRouter(tags=["reports"])

_reporter: ReportGenerator | None = None


def _get_reporter() -> ReportGenerator:
    global _reporter
    if _reporter is None:
        _reporter = ReportGenerator()
    return _reporter


@router.post("/v1/reports/generate")
def generate_report(request: ReportGenerateRequest, auth: AuthContext = Depends(get_auth)):
    """生成报告（日/周/月）"""
    reporter = _get_reporter()
    import uuid
    from datetime import datetime

    report_id = str(uuid.uuid4())

    if request.type == "daily":
        path = reporter.generate_daily()
    elif request.type == "weekly":
        path = reporter.generate_weekly()
    elif request.type == "monthly":
        path = reporter.generate_monthly()
    else:
        path = reporter.generate_daily()

    return {
        "report_id": report_id,
        "status": "completed",
        "path": str(path),
        "type": request.type,
    }


@router.get("/v1/reports")
def list_reports(auth: AuthContext = Depends(get_auth)):
    """报告列表"""
    from pathlib import Path
    reporter = _get_reporter()
    reports_dir = reporter.reports_dir
    items = []
    if reports_dir.exists():
        for f in sorted(reports_dir.glob("*.md"), reverse=True):
            items.append(ReportMeta(
                id=f.stem,
                type=f.stem.split("_")[0] if "_" in f.stem else "unknown",
                title=f.stem,
                status="completed",
                created_at="",
            ))
    return {"reports": items[:10]}