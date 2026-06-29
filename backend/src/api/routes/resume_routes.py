"""
Resume routes blueprint.
Ownership: szbenyx

Endpoints:
  POST /v1/resume/parse - Parse resume text to structured data
  POST /v1/resume/upload - Upload resume file for parsing (MVP: text only)
"""
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth, optional_auth
from src.utils.quota import consume_with_boost, QUOTA_LIMITS, RESOURCE_RESUME_PARSE, get_remaining, build_upgrade_hint

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/parse", methods=["POST"])
@optional_auth
def parse_resume():
    """Parse resume text to structured data."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify(error="bad_request", message="resume text required"), 400

    user_id = g.get("user_id", "guest-anon")
    tier = g.get("user_tier", "guest")

    # Quota check
    quota_result = consume_with_boost(user_id, tier, RESOURCE_RESUME_PARSE)
    if not quota_result["ok"]:
        upgrade = build_upgrade_hint(tier, 0)
        return jsonify(error="quota_exceeded", message="当日简历解析配额已用尽", upgrade=upgrade), 429

    try:
        from src.agents.document_agents import run_document_analysis
        result = run_document_analysis("resume", text)
        if result is None:
            return jsonify(error="parse_failed", message="简历解析未返回结果"), 500
        return jsonify(extracted=result)
    except Exception as e:
        return jsonify(error="parse_failed", message=str(e)), 500


@resume_bp.route("/upload", methods=["POST"])
@require_auth
def upload_resume():
    """Upload resume file for parsing (MVP: accepts text content only)."""
    # TODO: implement file upload + PDF parsing when needed
    return jsonify(error="not_implemented", message="File upload will be available in a future phase"), 501
