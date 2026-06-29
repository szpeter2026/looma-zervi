"""
Resume routes blueprint.
Ownership: szbenyx

Endpoints:
  POST /v1/resume/upload    - Upload and parse a resume
  GET  /v1/resume/:id       - Get parsed resume data
  GET  /v1/resume/mine      - List current user's resumes
"""
from flask import Blueprint, request, jsonify, g

from src.api.auth.decorators import require_auth

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/upload", methods=["POST"])
@require_auth
def upload_resume():
    """Upload and parse a resume file."""
    # TODO: migrate resume parsing pipeline
    return jsonify(message="resume upload endpoint - migrate pipeline here"), 200


@resume_bp.route("/<resume_id>", methods=["GET"])
@require_auth
def get_resume(resume_id):
    """Get a parsed resume's data."""
    # TODO: migrate resume retrieval
    return jsonify(error="not_found", message="resume not found"), 404


@resume_bp.route("/mine", methods=["GET"])
@require_auth
def my_resumes():
    """List current user's uploaded resumes."""
    # TODO: migrate resume listing
    return jsonify(resumes=[])
