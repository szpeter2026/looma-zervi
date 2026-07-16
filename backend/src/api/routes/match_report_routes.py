"""
Match report routes — persist resume×JD match results.

Endpoints (under /v1/match-reports):
  POST   /                 create report from match results
  GET    /                 list current user's reports
  GET    /:id              report detail with items
  DELETE /:id              soft-delete report
"""
from __future__ import annotations

import logging

from flask import Blueprint, current_app, g, jsonify, request

from src.api.auth.decorators import require_auth
from src.compliance.audit import AuditLogger
from src.compliance.consent import require_consent
from src.reports.match_report_manager import MatchReportManager

logger = logging.getLogger("looma.match_report_routes")

match_report_bp = Blueprint("match_reports", __name__)


def _manager() -> MatchReportManager:
    return MatchReportManager(current_app._db)


@match_report_bp.route("", methods=["POST"])
@match_report_bp.route("/", methods=["POST"])
@require_auth
@require_consent("report_generate")
def create_match_report():
    body = request.get_json(silent=True) or {}
    matches = body.get("matches")
    if not isinstance(matches, list) or not matches:
        return jsonify(error="bad_request", message="matches 不能为空"), 400

    resume_text = (body.get("resume_text") or "").strip()
    title = (body.get("title") or "").strip()
    summary = (body.get("summary") or "").strip()
    resume_id = (body.get("resume_id") or "").strip()

    try:
        report = _manager().create_report(
            user_id=g.user_id,
            resume_text=resume_text,
            matches=matches,
            title=title,
            summary=summary,
            resume_id=resume_id,
        )
    except ValueError as e:
        return jsonify(error="bad_request", message=str(e)), 400
    except Exception as e:
        logger.exception("create match report failed")
        return jsonify(error="create_failed", message=str(e)), 500

    AuditLogger().log_from_request(
        actor=g.user_id,
        action="report_generate",
        resource_type="match_report",
        resource_id=report["id"],
        metadata={"total_jobs": report.get("metadata", {}).get("total_jobs", 0)},
    )
    return jsonify(report), 201


@match_report_bp.route("", methods=["GET"])
@match_report_bp.route("/", methods=["GET"])
@require_auth
def list_match_reports():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    data = _manager().list_user_reports(g.user_id, page=page, page_size=page_size)
    return jsonify(data)


@match_report_bp.route("/<report_id>", methods=["GET"])
@require_auth
def get_match_report(report_id: str):
    report = _manager().get_report(report_id, user_id=g.user_id)
    if not report:
        return jsonify(error="not_found", message="报告不存在"), 404
    AuditLogger().log_from_request(
        actor=g.user_id,
        action="report_view",
        resource_type="match_report",
        resource_id=report_id,
    )
    return jsonify(report)


@match_report_bp.route("/<report_id>", methods=["DELETE"])
@require_auth
def delete_match_report(report_id: str):
    ok = _manager().delete_report(report_id, user_id=g.user_id)
    if not ok:
        return jsonify(error="not_found", message="报告不存在"), 404
    AuditLogger().log_from_request(
        actor=g.user_id,
        action="report_delete",
        resource_type="match_report",
        resource_id=report_id,
    )
    return jsonify(ok=True, id=report_id)
