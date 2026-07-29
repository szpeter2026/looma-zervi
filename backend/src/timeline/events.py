"""Best-effort timeline writers — never raise into business callers."""
from __future__ import annotations

import logging
from typing import Any

from src.timeline.constants import (
    EVENT_KIND_ALLOW_DUPLICATE,
    FORBIDDEN_PAYLOAD_KEYS,
    HYPOTHESIS_WEIGHT_CAPS,
)

logger = logging.getLogger("looma.timeline")


def sanitize_payload(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower() in FORBIDDEN_PAYLOAD_KEYS:
            logger.warning("Timeline PII blocked: key=%s", key)
            continue
        if isinstance(value, str) and len(value) > 2000:
            value = value[:2000]
        safe[key] = value
    return safe


def hypothesis_weight_cap(active_months: float) -> float:
    for months, cap in HYPOTHESIS_WEIGHT_CAPS:
        if active_months <= months:
            return cap
    return 0.1


def record_timeline_event(db, user_id: str, event_kind: str, source_system: str, **kwargs) -> dict | None:
    """Best-effort insert; returns row dict or None on failure."""
    try:
        payload = sanitize_payload(kwargs.pop("payload", None))
        allow_duplicate = kwargs.pop(
            "allow_duplicate",
            event_kind in EVENT_KIND_ALLOW_DUPLICATE,
        )
        return db.insert_timeline_event(
            user_id=user_id,
            event_kind=event_kind,
            source_system=source_system,
            payload=payload,
            allow_duplicate=allow_duplicate,
            **kwargs,
        )
    except Exception as e:
        logger.warning("record_timeline_event failed: %s %s", event_kind, e)
        return None


def record_quiz_hypothesis(
    db,
    user_id: str,
    personality_type: str,
    *,
    personality_detail: Any = None,
    source_ref: str | None = None,
) -> None:
    """Write quiz_completed + initial_hypothesis after profile-sync.

    Does not replace trust_memory or product_events — additive only.
    """
    ref = source_ref or f"profile_sync_{user_id}"
    detail_chars = 0
    if isinstance(personality_detail, str):
        detail_chars = len(personality_detail)
    elif personality_detail is not None:
        detail_chars = len(str(personality_detail))

    record_timeline_event(
        db,
        user_id,
        "quiz_completed",
        "quiz",
        source_ref=ref,
        title="完成星际人格测评",
        summary=f"测评结果：{personality_type}" if personality_type else "完成测评",
        payload={
            "personality_type": personality_type,
            "detail_chars": detail_chars,
        },
        signal_quality="observed",
        confidence=0.9,
        weight_role="evidence",
        visibility="private",
    )
    record_timeline_event(
        db,
        user_id,
        "initial_hypothesis",
        "quiz",
        source_ref=ref,
        title="初始假设（人格冷启动）",
        summary="测评结果仅为初始假设，将随行为沉淀被修正",
        payload={
            "personality_type": personality_type,
            "personality_detail_ref": "game_profiles",
            "label": "initial_hypothesis",
            "decay_class": "bei_like",
        },
        signal_quality="hypothesis",
        confidence=0.4,
        weight_role="hypothesis",
        visibility="private",
    )


def serialize_timeline_row(row: dict) -> dict:
    """DB row → API shape."""
    import json

    payload = row.get("payload_json") or "{}"
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (json.JSONDecodeError, TypeError):
            payload = {}
    consent = row.get("consent_scope") or "[]"
    if isinstance(consent, str):
        try:
            consent = json.loads(consent)
        except (json.JSONDecodeError, TypeError):
            consent = []
    return {
        "id": row.get("id"),
        "user_id": row.get("user_id"),
        "event_kind": row.get("event_kind"),
        "occurred_at": row.get("occurred_at"),
        "recorded_at": row.get("recorded_at"),
        "source_system": row.get("source_system"),
        "source_ref": row.get("source_ref") or "",
        "title": row.get("title") or "",
        "summary": row.get("summary") or "",
        "payload": payload,
        "signal_quality": row.get("signal_quality"),
        "confidence": row.get("confidence"),
        "weight_role": row.get("weight_role"),
        "visibility": row.get("visibility"),
        "consent_scope": consent,
        "status": row.get("status"),
        "superseded_by": row.get("superseded_by"),
    }


def compute_growth_stub(db, user_id: str) -> dict:
    """Minimal growth response — honest low confidence when sparse."""
    events = db.list_timeline_events(user_id, limit=100)
    active = [e for e in events if e.get("status") == "active"]
    n = len(active)
    kinds = {e.get("event_kind") for e in active}
    has_hypothesis = "initial_hypothesis" in kinds
    evidence_n = sum(1 for e in active if e.get("weight_role") == "evidence")

    if n < 3:
        confidence = "low"
        message = "行为沉淀不足，成长曲线仅供参考；完成每周签到或记录项目后会更准"
    elif n < 8:
        confidence = "medium"
        message = "已有初步行为节点，画像仍在浮现中"
    else:
        confidence = "building"
        message = "行为时间线正在变厚"

    # Rule-of-thumb dimensions (0-5) — not a real model yet
    action_density = min(5, evidence_n)
    exploration = min(5, len(kinds))
    expression = min(5, sum(1 for e in active if e.get("event_kind") in (
        "project_record", "interaction_log", "check_in",
    )))

    active_months = 0.0
    if active:
        # crude: count distinct YYYY-MM
        months = set()
        for e in active:
            ts = (e.get("occurred_at") or "")[:7]
            if len(ts) == 7:
                months.add(ts)
        active_months = float(len(months))

    return {
        "confidence": confidence,
        "message": message,
        "event_count": n,
        "hypothesis_present": has_hypothesis,
        "hypothesis_weight_cap": hypothesis_weight_cap(active_months or 0.5),
        "dimensions": [
            {"id": "action_density", "label": "行动密度", "level": action_density},
            {"id": "exploration", "label": "探索广度", "level": exploration},
            {"id": "expression", "label": "表达沉淀", "level": expression},
        ],
        "version": "growth_stub_v0",
    }
