"""
Reports routes blueprint.
Ownership: szbenyx

Endpoints:
  POST /v1/reports/generate - Generate a daily/weekly/monthly report
  GET  /v1/reports/list     - List generated reports
"""
from flask import Blueprint, request, jsonify, current_app, g

from src.api.auth.decorators import require_auth

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/generate", methods=["POST"])
@require_auth
def generate_report():
    """Generate a report (daily/weekly/monthly)."""
    data = request.get_json() or {}
    report_type = data.get("type", "daily")

    if report_type not in ("daily", "weekly", "monthly"):
        return jsonify(error="bad_request", message="type must be daily, weekly, or monthly"), 400

    try:
        from src.pipeline.report_gen import ReportGenerator
        reporter = ReportGenerator()
        path = reporter.generate_report(report_type)
        return jsonify(type=report_type, path=str(path), status="generated")
    except Exception as e:
        return jsonify(error="generate_failed", message=str(e)), 500


@reports_bp.route("/list", methods=["GET"])
@require_auth
def list_reports():
    """List generated reports (MVP: returns empty list)."""
    # TODO: implement report listing from reports directory
    return jsonify(reports=[], total=0)
