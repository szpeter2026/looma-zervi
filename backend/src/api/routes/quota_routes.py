"""
Quota routes blueprint.
Ownership: JOINT (dual review)

Endpoints:
  GET /v1/quota  - Get current user's daily quota usage
"""
from flask import Blueprint, jsonify, current_app, g

from src.api.auth.decorators import require_auth

quota_bp = Blueprint("quota", __name__)


@quota_bp.route("/quota", methods=["GET"])
@require_auth
def get_quota():
    """Get current user's daily quota usage and limits."""
    db = current_app._db
    used = db.get_daily_usage_count(g.user_id)
    limit = current_app.config["FREE_DAILY_LIMIT"]

    tier = g.get("user_tier", "free")
    if tier in ("supporter", "pro"):
        limit = 999999

    return jsonify(
        used=used,
        limit=limit,
        remaining=max(0, limit - used),
        tier=tier,
        reset_at="00:00 UTC+8 next day",
    )
