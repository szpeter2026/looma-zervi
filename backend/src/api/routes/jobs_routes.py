"""
Jobs routes blueprint.
Ownership: szbenyx (primary)

Endpoints:
  GET  /v1/jobs/         - List jobs
  GET  /v1/jobs/:id      - Get job detail
  POST /v1/jobs/match    - Match jobs based on personality/profile
"""
from flask import Blueprint, request, jsonify, g

from src.api.auth.decorators import require_auth

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/", methods=["GET"])
@require_auth
def list_jobs():
    """List available jobs."""
    # TODO: migrate jobs listing logic
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 20))
    return jsonify(jobs=[], total=0, page=page, size=size)


@jobs_bp.route("/<job_id>", methods=["GET"])
@require_auth
def get_job(job_id):
    """Get a specific job's details."""
    # TODO: migrate job detail logic
    return jsonify(error="not_found", message="job not found"), 404


@jobs_bp.route("/match", methods=["POST"])
@require_auth
def match_jobs():
    """Match jobs based on user's personality type and profile."""
    data = request.get_json() or {}
    # TODO: implement job matching based on personality_type
    return jsonify(matches=[], total=0)
