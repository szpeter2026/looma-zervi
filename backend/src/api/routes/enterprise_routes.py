"""
Enterprise routes blueprint.
Ownership: szbenyx

Endpoints:
  GET  /v1/enterprise/users          - List enterprise users
  GET  /v1/enterprise/candidate/:id  - Get candidate profile
  POST /v1/enterprise/invite         - Invite a candidate
  GET  /v1/enterprise/usage          - Get tenant usage stats
"""
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth

enterprise_bp = Blueprint("enterprise", __name__)


def _get_db():
    return current_app._db


@enterprise_bp.route("/users", methods=["GET"])
@require_auth
def list_users():
    """List all users in the current user's enterprise."""
    # TODO: implement enterprise_users lookup
    return jsonify(users=[])


@enterprise_bp.route("/candidate/<candidate_id>", methods=["GET"])
@require_auth
def get_candidate(candidate_id):
    """Get a candidate's profile (HR view)."""
    # TODO: implement candidate lookup with personality data
    return jsonify(error="not_found", message="candidate not found"), 404


@enterprise_bp.route("/invite", methods=["POST"])
@require_auth
def invite_candidate():
    """Invite a job seeker to become a candidate."""
    data = request.get_json() or {}
    # TODO: implement invite logic
    return jsonify(message="invitation sent")


@enterprise_bp.route("/usage", methods=["GET"])
@require_auth
def usage_stats():
    """Get the current enterprise's usage statistics."""
    # TODO: implement usage aggregation
    return jsonify(
        total_users=0,
        total_candidates=0,
        total_queries=0,
    )
