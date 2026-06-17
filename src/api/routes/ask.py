"""Looma api — 路由：/v1/ask 单入口 + 中央大脑意图分发"""
from __future__ import annotations

import time
import asyncio
import hashlib
import json
import logging
from collections import OrderedDict

from fastapi import APIRouter, Depends, HTTPException

from src.core.config import get_settings

from src.api.models import AskRequest, AskResponse, SourceNode, Intent, ExecutedOn
from src.api.auth import AuthContext, get_auth
from src.api.quota import consume, RESOURCE_ASK
from src.agents.central_brain import parse_intent, dispatch

logger = logging.getLogger("looma.ask")
router = APIRouter(tags=["ask"])

# ── 端到端剖析：结构化时序日志 ──
_PROFILE_ENABLED = True  # 设为 False 可关闭剖析日志


def _profile_log(query: str, intent: str, segments: dict, total_ms: int) -> None:
    """输出一条结构化剖析日志，key=profile 便于 grep/聚合。"""
    if not _PROFILE_ENABLED:
        return
    seg_str = " ".join(f"{k}={v}ms" for k, v in segments.items())
    logger.info(f"[profile] query={query[:60]!r} intent={intent} total={total_ms}ms {seg_str}")

# ── 请求级结果缓存（相同 query 秒级返回，压测核心优化）──
_result_cache: OrderedDict[str, tuple[float, dict]] = OrderedDict()
_RESULT_CACHE_MAX = 64
_RESULT_CACHE_TTL = 120  # 2 分钟


def _cache_key(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()


def _cache_get(query: str) -> dict | None:
    key = _cache_key(query)
    if key in _result_cache:
        ts, val = _result_cache[key]
        if time.time() - ts < _RESULT_CACHE_TTL:
            _result_cache.move_to_end(key)
            return val
        del _result_cache[key]
    return None


def _cache_set(query: str, result: dict) -> None:
    key = _cache_key(query)
    if key in _result_cache:
        _result_cache.move_to_end(key)
    _result_cache[key] = (time.time(), result)
    while len(_result_cache) > _RESULT_CACHE_MAX:
        _result_cache.popitem(last=False)


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
    """
    # 配额检查
    if not consume(auth.user_id, auth.tier, RESOURCE_ASK):
        raise HTTPException(status_code=429, detail={"code": "quota_exceeded", "message": "当日配额已用尽"})

    if auth.tier == "free" and req.context_scope.value not in ("public",):
        raise HTTPException(status_code=403, detail={
            "code": "scope_forbidden",
            "message": "当前免费版仅支持 context_scope=public",
        })

    t0 = time.time()
    profile_segments: dict[str, int] = {}  # 毫秒取整

    # ── 请求级缓存检查（相同 query 直接返回，压测核心优化）──
    cached_result = _cache_get(req.query)
    if cached_result is not None:
        elapsed = int((time.time() - t0) * 1000)
        logger.info(f"[cache HIT] {req.query[:50]!r} -> {cached_result['intent']} ({elapsed}ms)")
        return AskResponse(
            answer=cached_result["answer"],
            intent=_intent_to_model(cached_result["intent"]),
            sources=cached_result["sources"],
            executed_on=ExecutedOn.remote,
            context_scope=req.context_scope,
            tokens_used=elapsed,
        )

    # 1. 意图解析（线程池执行，避免 LLM 同步调用阻塞 event loop）
    t_intent = time.time()
    intent_str, confidence, slots = await asyncio.to_thread(parse_intent, req.query)
    profile_segments["intent"] = int((time.time() - t_intent) * 1000)
    logger.info(f"意图: {req.query[:50]!r} -> {intent_str} conf={confidence:.2f} ({profile_segments['intent']}ms)")

    # 2. 分发（线程池执行）— dispatch 内部会补充子段计时到 _timing dict
    t_dispatch = time.time()
    _timing: dict[str, int] = {}
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                dispatch,
                intent=intent_str,
                query=req.query,
                context=req.model_dump(),
                slots=slots,
                resume_text=None,
                _timing=_timing,
            ),
            timeout=get_settings().API_REQUEST_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail={
            "code": "request_timeout",
            "message": f"请求超过 {get_settings().API_REQUEST_TIMEOUT}s，上游服务无响应",
        })
    profile_segments["dispatch"] = int((time.time() - t_dispatch) * 1000)
    # 合并 dispatch 内部子段（rag_setup / rag_query / rag_llm 等）
    profile_segments.update(_timing)

    # 3. 提取 sources
    t_sources = time.time()
    sources_raw = result.get("_sources") or result.get("sources") or []
    sources = [
        SourceNode(
            chunk_text=(s.get("chunk_text", "") if isinstance(s, dict) else str(s))[:200],
            score=s.get("score") if isinstance(s, dict) else None,
        )
        for s in sources_raw
    ]
    profile_segments["sources_extract"] = int((time.time() - t_sources) * 1000)

    elapsed = int((time.time() - t0) * 1000)
    answer_text = result.get("answer") or result.get("message", "")

    # 缓存结果
    _cache_set(req.query, {
        "intent": intent_str,
        "answer": answer_text,
        "sources": sources,
    })

    # ── 结构化剖析日志 ──
    _profile_log(req.query, intent_str, profile_segments, elapsed)
    logger.info(f"[cache MISS] {req.query[:50]!r} -> {intent_str} ({elapsed}ms)")

    return AskResponse(
        answer=answer_text,
        intent=_intent_to_model(intent_str),
        sources=sources,
        executed_on=ExecutedOn.remote,
        context_scope=req.context_scope,
        tokens_used=elapsed,
    )