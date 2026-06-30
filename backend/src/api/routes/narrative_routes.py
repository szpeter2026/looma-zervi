"""
Narrative routes blueprint — Phase 0 feedback collection.
Ownership: Jason

Endpoints:
  POST /v1/narrative/start    - Start a narrative session
  POST /v1/narrative/event    - Log an event during the session
  POST /v1/narrative/end      - Mark session complete/abandoned
  POST /v1/narrative/feedback - Submit convergence-point qualitative feedback
  GET  /v1/narrative/stats    - Admin: aggregated Phase 0 metrics
"""
import logging

from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth, optional_auth

logger = logging.getLogger("looma.narrative")
narrative_bp = Blueprint("narrative", __name__)

VALID_DOMAINS = {"职业域", "诗域", "自我域", "身份域", "信任域", "迷雾域",
                 "career", "poetry", "self", "identity", "trust", "unknown"}
VALID_EVENT_TYPES = {
    "domain_enter", "choice_made", "convergence_reached",
    "share_attempt", "replay",
}


def _get_db():
    return current_app._db


# ── Start session ──

@narrative_bp.route("/start", methods=["POST"])
@optional_auth
def start_session():
    """Start a new narrative session. Guests can play (no auth required)."""
    data = request.get_json() or {}
    domain = data.get("domain", "").strip()

    if not domain:
        return jsonify(error="bad_request", message="domain required"), 400

    if domain not in VALID_DOMAINS:
        return jsonify(error="bad_request", message=f"unknown domain: {domain}"), 400

    user_id = g.get("user_id")  # None for guests

    db = _get_db()
    session_id = db.create_narrative_session(user_id, domain)

    logger.info(f"Narrative session started: {session_id} domain={domain} user={user_id}")
    return jsonify(session_id=session_id, domain=domain), 201


# ── Log event ──

@narrative_bp.route("/event", methods=["POST"])
@optional_auth
def log_event():
    """Log a narrative event within a session."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()
    event_type = data.get("event_type", "").strip()

    if not session_id or not event_type:
        return jsonify(error="bad_request", message="session_id and event_type required"), 400

    if event_type not in VALID_EVENT_TYPES:
        return jsonify(error="bad_request", message=f"unknown event_type: {event_type}"), 400

    db = _get_db()
    db.log_narrative_event(
        session_id=session_id,
        event_type=event_type,
        domain=data.get("domain"),
        choice=data.get("choice"),
        navigator_line=data.get("navigator_line"),
        metadata=data.get("metadata"),
    )

    return jsonify(ok=True, session_id=session_id, event_type=event_type)


# ── End session ──

@narrative_bp.route("/end", methods=["POST"])
@optional_auth
def end_session():
    """Mark a narrative session as completed or abandoned."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()
    completed = data.get("completed", False)
    duration_seconds = float(data.get("duration_seconds", 0))

    if not session_id:
        return jsonify(error="bad_request", message="session_id required"), 400

    status = "completed" if completed else "abandoned"

    db = _get_db()
    db.update_narrative_session(session_id, status, duration_seconds)

    logger.info(f"Narrative session {session_id} → {status} ({duration_seconds}s)")
    return jsonify(ok=True, session_id=session_id, status=status)


# ── Submit feedback ──

@narrative_bp.route("/feedback", methods=["POST"])
@optional_auth
def submit_feedback():
    """Submit convergence-point qualitative feedback.

    Body:
      session_id        (required) - session from /start
      resonated         (required) - bool: did Navigator touch you?
      navigator_quote   (optional) - recalled Navigator line
      would_replay      (optional) - 0=no, 1=maybe, 2=yes
      shared            (optional) - bool: did user share?
      share_channel     (optional) - "wechat"|"moments"|"link"|"other"
      open_feedback     (optional) - free-text qualitative feedback
    """
    data = request.get_json() or {}
    session_id = data.get("session_id", "").strip()

    if not session_id:
        return jsonify(error="bad_request", message="session_id required"), 400

    resonated = data.get("resonated")
    if resonated is None:
        return jsonify(error="bad_request", message="resonated (bool) required"), 400

    would_replay = data.get("would_replay")
    if would_replay is not None and would_replay not in (0, 1, 2):
        return jsonify(error="bad_request", message="would_replay must be 0, 1, or 2"), 400

    db = _get_db()
    db.submit_narrative_feedback(
        session_id=session_id,
        resonated=bool(resonated),
        navigator_quote=data.get("navigator_quote"),
        would_replay=would_replay,
        shared=bool(data.get("shared", False)),
        share_channel=data.get("share_channel"),
        open_feedback=data.get("open_feedback"),
    )

    logger.info(f"Narrative feedback submitted: {session_id} resonated={resonated}")
    return jsonify(ok=True, session_id=session_id), 201


# ── Stats (admin) ──

@narrative_bp.route("/stats", methods=["GET"])
@require_auth
def get_stats():
    """Get aggregated Phase 0 metrics. Admin only."""
    if g.get("user_role") != "admin":
        return jsonify(error="forbidden", message="admin only"), 403

    db = _get_db()
    stats = db.get_narrative_stats()
    return jsonify(stats)
