"""
Enterprise routes blueprint (T空间 B-end).
Ownership: szbenyx

Endpoints:
  POST /v1/enterprise/create      - Create an enterprise
  POST /v1/enterprise/join        - Join an enterprise
  GET  /v1/enterprise/profile     - Get enterprise profile
  GET  /v1/enterprise/candidates  - List candidates for enterprise
  POST /v1/enterprise/candidates/add - Add a candidate
"""
import uuid
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth, require_tier

enterprise_bp = Blueprint("enterprise", __name__)


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

        return jsonify(candidates=[dict(r) for r in rows])
    except Exception as e:
        return jsonify(error="list_failed", message=str(e)), 500


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
