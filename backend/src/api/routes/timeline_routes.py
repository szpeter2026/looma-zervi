"""
Career Timeline API — /v1/timeline/*

See docs/TIMELINE_EVENT_MODEL.md and contracts/timeline.v1.json.
"""
from __future__ import annotations

import logging

from flask import Blueprint, current_app, g, jsonify, request

from src.api.auth.decorators import require_auth
from src.timeline.constants import EVENT_KIND_MANUAL
from src.timeline.events import (
    compute_growth_stub,
    record_quiz_hypothesis,
    sanitize_payload,
    serialize_timeline_row,
)

logger = logging.getLogger("looma.timeline_routes")

timeline_bp = Blueprint("timeline", __name__)


def _get_db():
    return current_app._db


def _error(msg: str, code: str, status: int = 400):
    return jsonify(error=code, message=msg), status


@timeline_bp.route("", methods=["GET"])
@timeline_bp.route("/", methods=["GET"])
@require_auth
def list_timeline():
    """List current user's career timeline (newest first)."""
    db = _get_db()
    kind = (request.args.get("kind") or "").strip() or None
    since = (request.args.get("since") or "").strip() or None
    cursor = (request.args.get("cursor") or "").strip() or None
    try:
        limit = int(request.args.get("limit") or 50)
    except (TypeError, ValueError):
        limit = 50

    rows = db.list_timeline_events(
        g.user_id,
        event_kind=kind,
        since=since,
        cursor=cursor,
        limit=limit,
    )
    items = [serialize_timeline_row(r) for r in rows]
    next_cursor = items[-1]["occurred_at"] if len(items) >= limit else None
    return jsonify(items=items, next_cursor=next_cursor, count=len(items))


@timeline_bp.route("/events", methods=["POST"])
@require_auth
def create_timeline_event():
    """Manual write: project_record / check_in / career_decision only."""
    data = request.get_json() or {}
    event_kind = (data.get("event_kind") or "").strip()
    if event_kind not in EVENT_KIND_MANUAL:
        return _error(
            f"manual write only allows: {', '.join(sorted(EVENT_KIND_MANUAL))}",
            "invalid_event_kind",
        )

    title = (data.get("title") or "").strip()
    summary = (data.get("summary") or "").strip()
    payload = sanitize_payload(data.get("payload") if isinstance(data.get("payload"), dict) else {})
    occurred_at = (data.get("occurred_at") or "").strip() or None
    visibility = (data.get("visibility") or "private").strip()

    db = _get_db()
    row = db.insert_timeline_event(
        user_id=g.user_id,
        event_kind=event_kind,
        source_system="manual",
        source_ref=(data.get("source_ref") or "").strip(),
        title=title or event_kind,
        summary=summary,
        payload=payload,
        signal_quality="self_report",
        confidence=0.45,
        weight_role="evidence",
        visibility=visibility if visibility in ("private", "l1", "l2", "l3") else "private",
        occurred_at=occurred_at,
        allow_duplicate=(event_kind == "check_in"),
    )
    return jsonify(serialize_timeline_row(row)), 201


@timeline_bp.route("/events/<event_id>", methods=["PATCH"])
@require_auth
def patch_timeline_event(event_id: str):
    """Supersede with corrected title/summary/payload."""
    data = request.get_json() or {}
    db = _get_db()
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else None
    if payload is not None:
        payload = sanitize_payload(payload)
    new_row = db.supersede_timeline_event(
        g.user_id,
        event_id,
        title=data.get("title"),
        summary=data.get("summary"),
        payload=payload,
    )
    if not new_row:
        return _error("event not found", "not_found", 404)
    return jsonify(serialize_timeline_row(new_row))


@timeline_bp.route("/events/<event_id>", methods=["DELETE"])
@require_auth
def delete_timeline_event(event_id: str):
    db = _get_db()
    ok = db.soft_delete_timeline_event(g.user_id, event_id)
    if not ok:
        return _error("event not found", "not_found", 404)
    return jsonify(ok=True, id=event_id)


@timeline_bp.route("/growth", methods=["GET"])
@require_auth
def get_growth():
    """Minimal growth curve — honest low confidence when sparse."""
    db = _get_db()
    return jsonify(compute_growth_stub(db, g.user_id))


@timeline_bp.route("/bridge/backfill", methods=["POST"])
@require_auth
def bridge_backfill():
    """Idempotent: project existing quiz personality into timeline."""
    db = _get_db()
    profile = db.get_game_profile(g.user_id) or {}
    personality_type = (profile.get("personality_type") or "").strip()
    written = []
    if personality_type:
        record_quiz_hypothesis(
            db,
            g.user_id,
            personality_type,
            personality_detail=profile.get("personality_detail"),
            source_ref=f"profile_sync_{g.user_id}",
        )
        written.extend(["quiz_completed", "initial_hypothesis"])

    # Future: match_reports / share_codes / resume — E1.2+
    count = db.count_timeline_events(g.user_id)
    return jsonify(
        ok=True,
        written_kinds=written,
        event_count=count,
        note="phase1 backfill covers quiz hypothesis only; match/share/resume follow in E1.2+",
    )
