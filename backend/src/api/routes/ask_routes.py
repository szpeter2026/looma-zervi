"""
Ask routes blueprint (RAG knowledge base + central brain intent dispatch).
Ownership: szbenyx

Endpoints:
  POST /v1/ask   - Ask a question with RAG-powered answer + intent dispatch
  POST /v1/feedback/rate  - Rate a previous query (1-5)
  GET  /v1/feedback/last-query - Get user's last query ID
"""
from __future__ import annotations
import time
import hashlib
import logging
from collections import OrderedDict

from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth, optional_auth
from src.compliance.consent import require_consent
from src.utils.quota import (
    consume_with_boost, refund_consumption, get_remaining, build_upgrade_hint,
    QUOTA_LIMITS, RESOURCE_ASK,
)
from src.timeline.events import record_interaction_log

logger = logging.getLogger("looma.ask")

ask_bp = Blueprint("ask", __name__)

# ── LRU result cache (dedup identical queries within 2 min) ──
_result_cache: OrderedDict[str, tuple[float, dict]] = OrderedDict()
_RESULT_CACHE_MAX = 64
_RESULT_CACHE_TTL = 120


def _cache_key(query: str, mode: str = "chat") -> str:
    return hashlib.sha256(f"{mode}\n{query}".encode()).hexdigest()


def _cache_get(query: str, mode: str = "chat") -> dict | None:
    key = _cache_key(query, mode)
    if key in _result_cache:
        ts, val = _result_cache[key]
        if time.time() - ts < _RESULT_CACHE_TTL:
            _result_cache.move_to_end(key)
            return val
        del _result_cache[key]
    return None


def _cache_set(query: str, result: dict, mode: str = "chat") -> None:
    key = _cache_key(query, mode)
    if key in _result_cache:
        _result_cache.move_to_end(key)
    _result_cache[key] = (time.time(), result)
    while len(_result_cache) > _RESULT_CACHE_MAX:
        _result_cache.popitem(last=False)


@ask_bp.route("/ask", methods=["POST"])
@optional_auth
@require_consent("ask_rag")
def ask_question():
    """
    Ask a question → intent dispatch → RAG/poetry/MBTI/job match etc.
    Free/guest users have daily quota; supporter/pro unlimited.
    """
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    raw_mode = str(data.get("mode") or "chat").strip().lower()
    ask_mode = raw_mode if raw_mode in ("chat", "deepseek", "fast") else "chat"
    navigator_mode = data.get("navigator_mode", False)
    navigator_system_prompt = data.get("navigator_system_prompt")
    session_history = data.get("session_history")
    current_stage = data.get("current_stage")
    active_domain = data.get("active_domain")

    if not query:
        return jsonify(error="bad_request", message="query required"), 400

    user_id = g.get("user_id", "guest-anon")
    tier = g.get("user_tier", "guest")

    # Cache before quota — identical questions within TTL should not burn daily asks
    cached = _cache_get(query, ask_mode)
    if cached is not None:
        logger.info(f"[cache HIT] mode={ask_mode} {query[:50]!r}")
        # Still record timeline evidence (cache hits are real user interactions)
        if user_id and user_id != "guest-anon":
            try:
                record_interaction_log(
                    current_app._db,
                    user_id,
                    query=query,
                    intent=str(cached.get("intent") or ""),
                    intent_confidence=float(cached.get("intent_confidence") or 0),
                    response_time_ms=0,
                    ask_mode=ask_mode,
                )
            except Exception:
                pass
        return jsonify(
            answer=cached["answer"],
            intent=cached["intent"],
            intent_confidence=cached.get("intent_confidence"),
            sources=cached["sources"],
            mode=ask_mode,
        )

    quota_result = consume_with_boost(user_id, tier, RESOURCE_ASK)
    if not quota_result["ok"]:
        used = QUOTA_LIMITS.get(tier, QUOTA_LIMITS["guest"]).get(RESOURCE_ASK, 0)
        remaining = get_remaining(user_id, tier, RESOURCE_ASK)
        used_actual = used - remaining
        upgrade = build_upgrade_hint(tier, used_actual)
        return jsonify(
            error="quota_exceeded",
            message="当日配额已用尽",
            upgrade=upgrade,
        ), 429

    t0 = time.time()
    _timing: dict[str, int] = {}

    try:
        # Intent parsing
        from src.agents.central_brain import parse_intent, dispatch
        t_intent = time.time()
        intent_str, confidence, slots = parse_intent(query, navigator_mode=navigator_mode)
        _timing["intent"] = int((time.time() - t_intent) * 1000)
        logger.info(f"意图: {query[:50]!r} -> {intent_str} conf={confidence:.2f} ({_timing['intent']}ms)")

        # Dispatch
        t_dispatch = time.time()
        context = {
            "ask_mode": ask_mode,
            "navigator_mode": navigator_mode,
            "navigator_system_prompt": navigator_system_prompt,
            "session_history": session_history,
            "current_stage": current_stage,
            "active_domain": active_domain,
        }
        result = dispatch(
            intent=intent_str,
            query=query,
            context=context,
            slots=slots,
            _timing=_timing,
        )
        _timing["dispatch"] = int((time.time() - t_dispatch) * 1000)
    except Exception:
        logger.exception("ask dispatch failed; refunding quota")
        refund_consumption(user_id, RESOURCE_ASK, quota_result.get("source", "daily"))
        return jsonify(error="server_error", message="问答服务暂时不可用，请稍后重试"), 500

    elapsed = int((time.time() - t0) * 1000)
    logger.info(f"[cache MISS] {query[:50]!r} -> {intent_str} ({elapsed}ms)")

    # Build response
    sources_raw = result.get("_sources") or result.get("sources") or []
    sources = [
        {"chunk_text": s.get("chunk_text", "")[:200] if isinstance(s, dict) else str(s)[:200],
         "score": s.get("score") if isinstance(s, dict) else None}
        for s in sources_raw
    ]

    answer = result.get("answer") or result.get("message") or ""
    extracted = result.get("extracted")

    # Cache the result
    _cache_set(query, {
        "intent": intent_str,
        "intent_confidence": confidence,
        "answer": answer,
        "sources": sources,
    }, ask_mode)

    # Log query for data flywheel
    try:
        db = current_app._db
        db.log_query(
            query_text=query,
            provider="deepseek",
            response_time_ms=elapsed,
            chunk_count=len(sources),
            user_id=user_id if tier != "guest" else None,
            intent_label=intent_str,
        )
        # Timeline: AI interaction (best-effort, non-blocking)
        if user_id and user_id != "guest-anon":
            record_interaction_log(
                db,
                user_id,
                query=query,
                intent=intent_str,
                intent_confidence=round(confidence, 3),
                response_time_ms=elapsed,
                ask_mode=ask_mode,
            )
    except Exception:
        pass

    return jsonify(
        answer=answer,
        intent=intent_str,
        intent_confidence=round(confidence, 3),
        sources=sources,
        tokens_used=elapsed,
        extracted=extracted,
        mode=ask_mode,
    )


@ask_bp.route("/feedback/rate", methods=["POST"])
@require_auth
def rate_query():
    """Rate a previous query (1-5)."""
    data = request.get_json() or {}
    query_id = data.get("query_id")
    rating = data.get("rating")

    if not query_id or rating is None:
        return jsonify(error="bad_request", message="query_id and rating required"), 400

    if rating < 1 or rating > 5:
        return jsonify(error="bad_request", message="rating must be 1-5"), 400

    try:
        db = current_app._db
        db.rate_query(int(query_id), int(rating))
        return jsonify(ok=True, query_id=query_id, rating=rating)
    except Exception as e:
        return jsonify(error="rate_failed", message=str(e)), 500


@ask_bp.route("/feedback/last-query", methods=["GET"])
@require_auth
def last_query():
    """Get user's most recent query ID (for feedback wall)."""
    try:
        db = current_app._db
        qid = db.get_last_query_id(g.user_id)
        if qid is None:
            return jsonify(has_query=False)
        return jsonify(has_query=True, query_id=qid)
    except Exception:
        return jsonify(has_query=False)
