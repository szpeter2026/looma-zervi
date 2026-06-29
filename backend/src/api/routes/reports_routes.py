"""
Reports routes blueprint.
Ownership: szbenyx

Endpoints:
  GET  /v1/reports/daily    - Get daily report
  GET  /v1/reports/weekly   - Get weekly report
  GET  /v1/reports/monthly  - Get monthly report
  POST /v1/reports/generate - Generate a custom report
"""
from flask import Blueprint, request, jsonify, g

from src.api.auth.decorators import require_auth, require_tier

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/daily", methods=["GET"])
@require_auth
def daily_report():
    """Get today's report for the current user."""
    # TODO: migrate daily report generation
    return jsonify(report=None, message="daily report endpoint - migrate logic here")


@reports_bp.route("/weekly", methods=["GET"])
@require_auth
def weekly_report():
    """Get this week's report."""
    # TODO: migrate weekly report generation
    return jsonify(report=None)


@reports_bp.route("/monthly", methods=["GET"])
@require_auth
def monthly_report():
    """Get this month's report."""
    # TODO: migrate monthly report generation
    return jsonify(report=None)


@reports_bp.route("/generate", methods=["POST"])
@require_auth
@require_tier("pro")
def generate_report():
    """Generate a custom deep-dive report (Pro tier only)."""
    data = request.get_json() or {}
    report_type = data.get("type", "personality_deep_dive")
    # TODO: migrate deep report generation logic
    return jsonify(report=None, type=report_type, message="generate endpoint - migrate logic here")
