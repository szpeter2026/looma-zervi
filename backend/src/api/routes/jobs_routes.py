"""
Jobs routes blueprint.
Ownership: szbenyx

Endpoints:
  POST /v1/jobs/match  - Match resume to job listings
  GET  /v1/jobs/list   - List available jobs (MVP: mock data)
"""
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth, optional_auth
from src.utils.quota import consume_with_boost, QUOTA_LIMITS, RESOURCE_JOB_MATCH, get_remaining, build_upgrade_hint

jobs_bp = Blueprint("jobs", __name__)


@jobs_bp.route("/match", methods=["POST"])
@optional_auth
def job_match():
    """Match a resume to job listings via LLM scoring."""
    data = request.get_json() or {}
    resume_text = data.get("resume_text", "").strip()

    if not resume_text:
        return jsonify(error="bad_request", message="resume_text required"), 400

    user_id = g.get("user_id", "guest-anon")
    tier = g.get("user_tier", "guest")

    # Quota check
    quota_result = consume_with_boost(user_id, tier, RESOURCE_JOB_MATCH)
    if not quota_result["ok"]:
        used = QUOTA_LIMITS.get(tier, QUOTA_LIMITS["guest"]).get(RESOURCE_JOB_MATCH, 0)
        remaining = get_remaining(user_id, tier, RESOURCE_JOB_MATCH)
        upgrade = build_upgrade_hint(tier, used - remaining)
        return jsonify(error="quota_exceeded", message="当日职位匹配配额已用尽", upgrade=upgrade), 429

    try:
        from src.pipeline.job_match_pipeline import run_job_match_pipeline
        matches, total = run_job_match_pipeline(resume_text=resume_text)
        return jsonify(matches=matches, total_evaluated=total)
    except Exception as e:
        return jsonify(error="match_failed", message=str(e)), 500


@jobs_bp.route("/list", methods=["GET"])
@optional_auth
def list_jobs():
    """List available jobs (MVP: mock data)."""
    from src.pipeline.job_match_pipeline import MOCK_JOBS
    return jsonify(jobs=MOCK_JOBS, total=len(MOCK_JOBS))
