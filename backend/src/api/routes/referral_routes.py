"""
Referral routes blueprint.
Ownership: Jason (primary)

Endpoints:
  POST /v1/referral/generate  - Generate a referral link for HR
  GET  /v1/referral/:code     - Resolve a referral code
  GET  /v1/referral/mine      - List current user's referrals
"""
from flask import Blueprint, request, jsonify, g

from src.api.auth.decorators import require_auth

referral_bp = Blueprint("referral", __name__)


@referral_bp.route("/generate", methods=["POST"])
@require_auth
def generate_referral():
    """Generate a referral link for sharing with HR/headhunters."""
    data = request.get_json() or {}
    # TODO: implement referral link generation
    return jsonify(
        link="",
        code="",
        message="referral generation - implement here"
    )


@referral_bp.route("/<code>", methods=["GET"])
@require_auth
def resolve_referral(code):
    """Resolve a referral code to a candidate profile (HR view)."""
    # TODO: implement referral resolution
    return jsonify(error="not_found", message="referral code not found"), 404


@referral_bp.route("/mine", methods=["GET"])
@require_auth
def my_referrals():
    """List current user's generated referrals."""
    # TODO: implement referral listing
    return jsonify(referrals=[])
