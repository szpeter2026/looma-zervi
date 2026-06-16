"""Looma api — 简历解析路由"""
from __future__ import annotations

import io
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.api.models import ResumeAnalysis
from src.api.auth import AuthContext, get_auth
from src.api.quota import consume, RESOURCE_RESUME_PARSE

router = APIRouter(tags=["resume"])


@router.post("/v1/resume/parse", response_model=ResumeAnalysis)
async def resume_parse(
    file: UploadFile = File(..., description="PDF/Word 简历文件"),
    auth: AuthContext = Depends(get_auth),
):
    """简历解析（结构化输出）"""
    if not consume(auth.user_id, auth.tier, RESOURCE_RESUME_PARSE):
        raise HTTPException(status_code=429, detail={"code": "quota_exceeded", "message": "当日配额已用尽"})

    try:
        content = await file.read()
        text = content.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取文件失败: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="文件为空")

    try:
        from src.agents.document_agents import run_document_analysis
        result = run_document_analysis("resume", text)
        data = result.model_dump()
        return ResumeAnalysis(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"简历解析失败: {e}")