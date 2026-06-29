"""
Referral routes blueprint.
Ownership: JOINT (dual review required)

Endpoints:
  POST /v1/referral/create   - Create a new invite code
  POST /v1/referral/use      - Consume an invite code
  GET  /v1/referral/my-codes - List user's created invite codes
"""
import uuid
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth

referral_bp = Blueprint("referral", __name__)


@referral_bp.route("/create", methods=["POST"])
@require_auth
def create_code():
    """Create a new invite code."""
    data = request.get_json() or {}
    tier_grant = data.get("tier_grant", "free")

    db = current_app._db
    code = str(uuid.uuid4())[:8].upper()  # Simple 8-char code

    try:
        with db.get_conn() as conn:
            conn.execute(
                """INSERT INTO invite_codes (id, code, created_by, tier_grant)
                   VALUES (?, ?, ?, ?)""",
                (str(uuid.uuid4()), code, g.user_id, tier_grant)
            )
        return jsonify(code=code, tier_grant=tier_grant), 201
    except Exception as e:
        return jsonify(error="create_failed", message=str(e)), 500


@referral_bp.route("/use", methods=["POST"])
@require_auth
def use_code():
    """Consume an invite code."""
    data = request.get_json() or {}
    code = data.get("code", "").strip().upper()

    if not code:
        return jsonify(error="bad_request", message="invite code required"), 400

    db = current_app._db

    try:
        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM invite_codes WHERE code = ? AND used_by IS NULL",
                (code,)
            ).fetchone()

            if not row:
                return jsonify(error="not_found", message="邀请码不存在或已被使用"), 404

            invite = dict(row)

            # Check expiry
            if invite.get("expires_at") and invite["expires_at"] < "now":
                return jsonify(error="expired", message="邀请码已过期"), 400

            # Use the code
            conn.execute(
                """UPDATE invite_codes SET used_by = ?, used_at = datetime('now')
                   WHERE code = ?""",
                (g.user_id, code)
            )

            # Grant tier if applicable
            if invite.get("tier_grant") and invite["tier_grant"] != "free":
                conn.execute(
                    "UPDATE users SET tier = ?, updated_at = datetime('now') WHERE id = ?",
                    (invite["tier_grant"], g.user_id)
                )

        return jsonify(consumed=True, code=code, tier_granted=invite.get("tier_grant", "free"))
    except Exception as e:
        return jsonify(error="use_failed", message=str(e)), 500


@referral_bp.route("/my-codes", methods=["GET"])
@require_auth
def my_codes():
    """List invite codes created by the current user."""
    db = current_app._db

    try:
        with db.get_conn() as conn:
            rows = conn.execute(
                """SELECT code, tier_grant, used_by, used_at, created_at
                   FROM invite_codes WHERE created_by = ?
                   ORDER BY created_at DESC""",
                (g.user_id,)
            ).fetchall()
        return jsonify(codes=[dict(r) for r in rows])
    except Exception as e:
        return jsonify(error="list_failed", message=str(e)), 500
