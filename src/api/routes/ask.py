"""Looma api — 路由：/v1/ask 免费体验入口"""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException

from src.api.models import AskRequest, AskResponse, SourceNode, Intent, ExecutedOn
from src.retrieval.rag_engine import get_index

router = APIRouter(tags=["ask"])


@router.post("/v1/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """免费体验单入口：RAG 检索 + LLM 生成回答"""
    index = get_index()
    if index is None:
        raise HTTPException(status_code=503, detail="知识库未就绪")

    t0 = time.time()

    # 1. 检索 top-3
    query_engine = index.as_query_engine(similarity_top_k=3)
    response = await query_engine.aquery(req.query)

    # 2. 收集来源
    sources = []
    for node in response.source_nodes:
        sources.append(SourceNode(
            chunk_text=node.text[:200],
            score=round(node.score, 4) if node.score else None,
        ))

    elapsed = int((time.time() - t0) * 1000)
    return AskResponse(
        answer=str(response),
        intent=Intent.rag,
        sources=sources,
        executed_on=ExecutedOn.remote,
        context_scope=req.context_scope,
        tokens_used=elapsed,  # P2: 实际应统计 token
    )
