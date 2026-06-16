"""Looma api — 路由：/v1/ask 单入口 + 中央大脑意图分发"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException

from src.api.models import AskRequest, AskResponse, SourceNode, Intent, ExecutedOn
from src.api.auth import AuthContext, get_auth
from src.api.quota import consume, RESOURCE_ASK
from src.agents.central_brain import parse_intent, dispatch
from src.retrieval.rag_engine import get_index

router = APIRouter(tags=["ask"])


def _intent_to_model(intent_str: str) -> Intent:
    """将内部意图字符串映射到 API 模型 Intent 枚举"""
    mapping = {
        "rag": Intent.rag,
        "resume_parse": Intent.resume_parse,
        "job_match": Intent.job_match,
        "credit": Intent.credit_analysis,
        "mbti": Intent.mbti,
        "poetry": Intent.poetry,
        "report": Intent.report,
        "unknown": Intent.unknown,
    }
    return mapping.get(intent_str, Intent.unknown)


@router.post("/v1/ask", response_model=AskResponse)
async def ask(req: AskRequest, auth: AuthContext = Depends(get_auth)):
    """
    单入口：用户需求由此进入，中央大脑解析意图并分发到内部端口，返回统一 JSON。
    支持所有业务能力：RAG、职位匹配、简历解析、诗词推荐、MBTI 测评、征信分析、报告生成。
    """
    # 配额检查
    if not consume(auth.user_id, auth.tier, RESOURCE_ASK):
        raise HTTPException(status_code=429, detail={"code": "quota_exceeded", "message": "当日配额已用尽"})

    t0 = time.time()

    # 1. 意图解析（LLM 主路径 + 规则回退）
    intent_str, confidence, slots = parse_intent(req.query)

    # 2. 分发到能力端口
    result = dispatch(
        intent=intent_str,
        query=req.query,
        context=req.model_dump(),
        slots=slots,
        resume_text=None,
    )

    # 3. 处理 RAG 意图的源码信息
    sources = []
    if intent_str == "rag":
        try:
            index = get_index()
            if index is not None:
                query_engine = index.as_query_engine(similarity_top_k=3)
                response = await query_engine.aquery(req.query)
                for node in response.source_nodes:
                    sources.append(SourceNode(
                        chunk_text=node.text[:200],
                        score=round(node.score, 4) if node.score else None,
                    ))
        except Exception:
            pass

    elapsed = int((time.time() - t0) * 1000)

    return AskResponse(
        answer=result.get("answer") or result.get("message", ""),
        intent=_intent_to_model(intent_str),
        sources=sources,
        executed_on=ExecutedOn.remote,
        context_scope=req.context_scope,
        tokens_used=elapsed,
    )