"""
Enterprise routes blueprint (T空间 B-end).
Ownership: szbenyx

Endpoints:
  POST /v1/enterprise/create              - Create an enterprise
  POST /v1/enterprise/join                - Join an enterprise
  GET  /v1/enterprise/profile             - Get enterprise profile
  GET  /v1/enterprise/candidates          - List candidates for enterprise
  GET  /v1/enterprise/candidate/<id>      - Get candidate detail (HR profile view)
  POST /v1/enterprise/candidates/add      - Add a candidate manually
  POST /v1/enterprise/candidates/import-share - Import candidate from PlanetX share code
"""
from __future__ import annotations

import json
import uuid
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth, require_tier
from src.analytics.events import (
    log_product_event,
    platform_from_request,
    EVENT_CANDIDATE_IMPORTED,
    EVENT_CANDIDATE_IMPORT_DUPLICATE,
)

enterprise_bp = Blueprint("enterprise", __name__)

PROFILE_SHARE_GRANT = "profile_share"


def _get_user_enterprise(conn, user_id: str):
    """Return (enterprise_id, role) or None."""
    row = conn.execute(
        "SELECT enterprise_id, role FROM enterprise_users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def _parse_profile_data(raw) -> dict | None:
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _candidate_response(row: dict) -> dict:
    result = dict(row)
    result["profile_data"] = _parse_profile_data(result.get("profile_data"))
    return result


@enterprise_bp.route("/create", methods=["POST"])
@require_auth
def create_enterprise():
    """Create a new enterprise (HR company/training org)."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    domain = data.get("domain", "").strip()

    if not name:
        return jsonify(error="bad_request", message="enterprise name required"), 400

    db = current_app._db
    enterprise_id = str(uuid.uuid4())

    try:
        with db.get_conn() as conn:
            conn.execute(
                """INSERT INTO enterprises (id, name, domain)
                   VALUES (?, ?, ?)""",
                (enterprise_id, name, domain)
            )
            # Creator becomes admin
            conn.execute(
                """INSERT INTO enterprise_users (id, enterprise_id, user_id, role)
                   VALUES (?, ?, ?, 'admin')""",
                (str(uuid.uuid4()), enterprise_id, g.user_id)
            )
        return jsonify(id=enterprise_id, name=name, domain=domain, role="admin"), 201
    except Exception as e:
        return jsonify(error="create_failed", message=str(e)), 500


@enterprise_bp.route("/join", methods=["POST"])
@require_auth
def join_enterprise():
    """Join an existing enterprise as member."""
    data = request.get_json() or {}
    enterprise_id = data.get("enterprise_id", "").strip()

    if not enterprise_id:
        return jsonify(error="bad_request", message="enterprise_id required"), 400

    db = current_app._db

    try:
        with db.get_conn() as conn:
            # Check enterprise exists
            row = conn.execute("SELECT id FROM enterprises WHERE id = ?", (enterprise_id,)).fetchone()
            if not row:
                return jsonify(error="not_found", message="企业不存在"), 404

            # Check not already a member
            existing = conn.execute(
                "SELECT id FROM enterprise_users WHERE enterprise_id = ? AND user_id = ?",
                (enterprise_id, g.user_id)
            ).fetchone()
            if existing:
                return jsonify(error="conflict", message="已经是该企业的成员"), 409

            conn.execute(
                """INSERT INTO enterprise_users (id, enterprise_id, user_id, role)
                   VALUES (?, ?, ?, 'member')""",
                (str(uuid.uuid4()), enterprise_id, g.user_id)
            )
        return jsonify(enterprise_id=enterprise_id, role="member")
    except Exception as e:
        return jsonify(error="join_failed", message=str(e)), 500


@enterprise_bp.route("/profile", methods=["GET"])
@require_auth
def enterprise_profile():
    """Get the enterprise the current user belongs to."""
    db = current_app._db

    try:
        with db.get_conn() as conn:
            row = conn.execute(
                """SELECT e.*, eu.role FROM enterprises e
                   JOIN enterprise_users eu ON e.id = eu.enterprise_id
                   WHERE eu.user_id = ?""",
                (g.user_id,)
            ).fetchone()

        if not row:
            return jsonify(error="not_found", message="不属于任何企业"), 404

        result = dict(row)
        return jsonify(result)
    except Exception as e:
        return jsonify(error="profile_failed", message=str(e)), 500


@enterprise_bp.route("/candidates", methods=["GET"])
@require_auth
def list_candidates():
    """List candidates for the current user's enterprise."""
    db = current_app._db

    try:
        with db.get_conn() as conn:
            # Find user's enterprise
            eu_row = conn.execute(
                "SELECT enterprise_id, role FROM enterprise_users WHERE user_id = ?",
                (g.user_id,)
            ).fetchone()

            if not eu_row:
                return jsonify(error="not_found", message="不属于任何企业"), 404

            enterprise_id = dict(eu_row)["enterprise_id"]

            rows = conn.execute(
                "SELECT * FROM candidates WHERE enterprise_id = ? ORDER BY created_at DESC",
                (enterprise_id,)
            ).fetchall()

        return jsonify(candidates=[_candidate_response(dict(r)) for r in rows])
    except Exception as e:
        return jsonify(error="list_failed", message=str(e)), 500


@enterprise_bp.route("/candidate/<candidate_id>", methods=["GET"])
@require_auth
def get_candidate(candidate_id: str):
    """Get a single candidate with full profile data (HR view)."""
    db = current_app._db

    try:
        with db.get_conn() as conn:
            eu = _get_user_enterprise(conn, g.user_id)
            if not eu:
                return jsonify(error="not_found", message="不属于任何企业"), 404

            row = conn.execute(
                "SELECT * FROM candidates WHERE id = ? AND enterprise_id = ?",
                (candidate_id, eu["enterprise_id"]),
            ).fetchone()

            if not row:
                return jsonify(error="not_found", message="候选人不存在"), 404

        return jsonify(_candidate_response(dict(row)))
    except Exception as e:
        return jsonify(error="get_failed", message=str(e)), 500


@enterprise_bp.route("/candidates/import-share", methods=["POST"])
@require_auth
def import_candidate_from_share():
    """Import a PlanetX job seeker into the enterprise via profile share code."""
    data = request.get_json() or {}
    share_code = data.get("share_code", "").strip().upper()

    if not share_code:
        return jsonify(error="bad_request", message="share_code required"), 400

    db = current_app._db

    try:
        with db.get_conn() as conn:
            eu = _get_user_enterprise(conn, g.user_id)
            if not eu:
                return jsonify(error="not_found", message="请先创建或加入企业"), 404

            enterprise_id = eu["enterprise_id"]

            invite = conn.execute(
                "SELECT * FROM invite_codes WHERE code = ? AND tier_grant = ?",
                (share_code, PROFILE_SHARE_GRANT),
            ).fetchone()
            if not invite:
                return jsonify(error="not_found", message="分享码无效"), 404

            invite = dict(invite)
            seeker_id = invite["created_by"]

            # Avoid duplicate import
            existing = conn.execute(
                """SELECT id FROM candidates
                   WHERE enterprise_id = ? AND user_id = ?""",
                (enterprise_id, seeker_id),
            ).fetchone()
            if existing:
                row = conn.execute(
                    "SELECT * FROM candidates WHERE id = ?",
                    (dict(existing)["id"],),
                ).fetchone()
                result = _candidate_response(dict(row))
                result["imported"] = False
                log_product_event(
                    db,
                    EVENT_CANDIDATE_IMPORT_DUPLICATE,
                    user_id=g.user_id,
                    share_code=share_code,
                    platform=platform_from_request(request),
                    source="server",
                )
                return jsonify(result), 200

            user_row = conn.execute(
                "SELECT id, name, email FROM users WHERE id = ?",
                (seeker_id,),
            ).fetchone()
            profile_row = conn.execute(
                "SELECT * FROM game_profiles WHERE user_id = ?",
                (seeker_id,),
            ).fetchone()

            if not profile_row:
                return jsonify(error="not_found", message="该求职者尚未完成人格测试"), 404

            user = dict(user_row) if user_row else {}
            profile = dict(profile_row)
            display_name = user.get("name") or user.get("email") or "求职者"
            if display_name and "@" in display_name:
                display_name = display_name.split("@")[0]

            detail = profile.get("personality_detail")
            profile_data = {
                "personality_type": profile.get("personality_type"),
                "personality_detail": _parse_profile_data(detail) or detail,
                "xp": profile.get("xp", 0),
                "level": profile.get("level", 1),
                "share_code": share_code,
            }

            candidate_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO candidates
                   (id, enterprise_id, user_id, name, email, profile_data, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'new')""",
                (
                    candidate_id,
                    enterprise_id,
                    seeker_id,
                    display_name,
                    user.get("email"),
                    json.dumps(profile_data, ensure_ascii=False),
                ),
            )

            row = conn.execute(
                "SELECT * FROM candidates WHERE id = ?",
                (candidate_id,),
            ).fetchone()

        result = _candidate_response(dict(row))
        result["imported"] = True
        log_product_event(
            db,
            EVENT_CANDIDATE_IMPORTED,
            user_id=g.user_id,
            share_code=share_code,
            platform=platform_from_request(request),
            source="server",
            properties={"candidate_id": candidate_id, "seeker_id": seeker_id},
        )
        return jsonify(result), 201
    except Exception as e:
        return jsonify(error="import_failed", message=str(e)), 500


@enterprise_bp.route("/candidates/add", methods=["POST"])
@require_auth
def add_candidate():
    """Add a candidate to the enterprise."""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "")
    phone = data.get("phone", "")
    profile_data = data.get("profile_data")

    if not name:
        return jsonify(error="bad_request", message="candidate name required"), 400

    db = current_app._db

    try:
        with db.get_conn() as conn:
            # Find user's enterprise
            eu_row = conn.execute(
                "SELECT enterprise_id FROM enterprise_users WHERE user_id = ?",
                (g.user_id,)
            ).fetchone()

            if not eu_row:
                return jsonify(error="not_found", message="不属于任何企业"), 404

            enterprise_id = dict(eu_row)["enterprise_id"]

            import json
            conn.execute(
                """INSERT INTO candidates (id, enterprise_id, name, email, phone, profile_data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(uuid.uuid4()), enterprise_id, name, email, phone,
                 json.dumps(profile_data) if profile_data else None)
            )

        return jsonify(name=name, email=email, status="new"), 201
    except Exception as e:
        return jsonify(error="add_failed", message=str(e)), 500
