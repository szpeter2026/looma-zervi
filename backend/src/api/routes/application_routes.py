"""
Job application routes — DemoPeter thin-ingest → HR-visible apply records.

Endpoints:
  POST   /v1/application              - Seeker applies resume_id to job_id
  GET    /v1/application              - Seeker lists own applications
  GET    /v1/application/<id>         - Get one (seeker owner or job HR)
  DELETE /v1/application/<id>         - Withdraw (HR no longer sees resume body)
  GET    /v1/jobs/<job_id>/applications - HR lists active applications for a job
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone, timedelta

from flask import Blueprint, current_app, g, jsonify, request

from src.api.auth.decorators import require_auth
from src.compliance.consent import require_consent

logger = logging.getLogger("looma.application")
application_bp = Blueprint("application", __name__)

_SHA_TZ = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(_SHA_TZ).strftime("%Y-%m-%dT%H:%M:%S%z")


def _db():
    from src.db.manager import DatabaseManager

    db_path = current_app.config.get("DATABASE_PATH", "data/looma.db")
    return DatabaseManager(db_path)


def _row_to_app(row) -> dict:
    d = dict(row)
    try:
        meta = json.loads(d.get("metadata") or "{}")
    except json.JSONDecodeError:
        meta = {}
    return {
        "id": d["id"],
        "seeker_user_id": d["seeker_user_id"],
        "resume_id": d["resume_id"],
        "job_id": d["job_id"],
        "enterprise_id": d.get("enterprise_id") or "",
        "status": d["status"],
        "metadata": meta if isinstance(meta, dict) else {},
        "created_at": d["created_at"],
        "updated_at": d["updated_at"],
        "withdrawn_at": d.get("withdrawn_at"),
    }


def _get_resume_owned(conn, resume_id: str, seeker_user_id: str):
    row = conn.execute(
        "SELECT id, title, metadata, status FROM documents WHERE id = ? AND doc_type = 'resume'",
        (resume_id,),
    ).fetchone()
    if not row:
        return None
    try:
        meta = json.loads(row["metadata"] or "{}")
    except json.JSONDecodeError:
        meta = {}
    if str(meta.get("user_id") or "") != str(seeker_user_id):
        return None
    return row, meta if isinstance(meta, dict) else {}


def _job_owner_user_id(conn, job_id: str) -> str | None:
    """Resolve owner for persisted job document or job_posts row."""
    # documents.metadata.job_id
    rows = conn.execute(
        """SELECT metadata FROM documents
           WHERE doc_type = 'job' AND status = 'processed'"""
    ).fetchall()
    for r in rows:
        try:
            meta = json.loads(r["metadata"] or "{}")
        except json.JSONDecodeError:
            continue
        jid = meta.get("job_id") or (meta.get("parsed") or {}).get("id")
        if str(jid) == str(job_id):
            return str(meta.get("user_id") or "") or None

    # job_posts.id
    jp = conn.execute(
        "SELECT user_id FROM job_posts WHERE id = ?", (job_id,)
    ).fetchone()
    if jp:
        return str(jp["user_id"])
    return None


def _job_exists(conn, job_id: str) -> bool:
    if _job_owner_user_id(conn, job_id) is not None:
        return True
    # Allow apply to known mock/demo ids even before seed (CN fixtures)
    from src.api.routes.jobs_routes import MOCK_JOBS

    return any(str(j["id"]) == str(job_id) for j in MOCK_JOBS)


def _can_view_as_hr(conn, viewer_user_id: str, job_id: str) -> bool:
    owner = _job_owner_user_id(conn, job_id)
    if owner and owner == str(viewer_user_id):
        return True
    user = conn.execute(
        "SELECT role FROM users WHERE id = ?", (viewer_user_id,)
    ).fetchone()
    if user and (user["role"] or "") in ("admin", "hr", "enterprise"):
        return True
    # Enterprise member linked to application.enterprise_id checked at call site
    return False


def _resume_payload_for_hr(meta: dict, *, include_body: bool) -> dict:
    """HR-visible resume summary; body only when application is active."""
    extracted = meta.get("extracted") if isinstance(meta.get("extracted"), dict) else {}
    out = {
        "filename": meta.get("filename") or "",
        "has_extracted": bool(extracted),
        "skills": (extracted or {}).get("skills") or [],
        "name": (extracted or {}).get("name"),
    }
    if include_body:
        md = meta.get("markdown") or ""
        out["markdown"] = md[:8000] if isinstance(md, str) else ""
        out["extracted"] = extracted
    else:
        out["markdown"] = None
        out["extracted"] = None
        out["redacted"] = True
    return out


@application_bp.route("/application", methods=["POST"])
@require_auth
@require_consent("application_submit")
def create_application():
    """Seeker: bind resume_id to job_id as a submitted application."""
    data = request.get_json() or {}
    resume_id = str(data.get("resume_id") or "").strip()
    job_id = str(data.get("job_id") or "").strip()
    enterprise_id = str(data.get("enterprise_id") or "").strip()
    if not resume_id or not job_id:
        return jsonify(error="bad_request", message="resume_id and job_id are required"), 400

    seeker = str(g.user_id)
    db = _db()
    now = _now_iso()

    with db.get_conn() as conn:
        owned = _get_resume_owned(conn, resume_id, seeker)
        if not owned:
            return jsonify(error="not_found", message="简历不存在或不属于当前用户"), 404
        _row, resume_meta = owned

        if not _job_exists(conn, job_id):
            return jsonify(error="not_found", message="职位不存在"), 404

        existing = conn.execute(
            """SELECT id, status FROM applications
               WHERE seeker_user_id = ? AND resume_id = ? AND job_id = ?
                 AND status = 'submitted'""",
            (seeker, resume_id, job_id),
        ).fetchone()
        if existing:
            return jsonify(
                application=_row_to_app(
                    conn.execute(
                        "SELECT * FROM applications WHERE id = ?", (existing["id"],)
                    ).fetchone()
                ),
                already_exists=True,
            ), 200

        app_id = str(uuid.uuid4())
        meta = {
            "source": data.get("source") or "api",
            "resume_title": _row["title"],
        }
        conn.execute(
            """INSERT INTO applications
               (id, seeker_user_id, resume_id, job_id, enterprise_id, status, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'submitted', ?, ?, ?)""",
            (
                app_id,
                seeker,
                resume_id,
                job_id,
                enterprise_id,
                json.dumps(meta, ensure_ascii=False),
                now,
                now,
            ),
        )
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()

    logger.info(
        "application created id=%s seeker=%s resume=%s job=%s",
        app_id,
        seeker,
        resume_id,
        job_id,
    )
    return jsonify(application=_row_to_app(row), already_exists=False), 201


@application_bp.route("/application", methods=["GET"])
@require_auth
def list_my_applications():
    """Seeker: list own applications (including withdrawn)."""
    seeker = str(g.user_id)
    status = (request.args.get("status") or "").strip()
    db = _db()
    with db.get_conn() as conn:
        if status:
            rows = conn.execute(
                """SELECT * FROM applications
                   WHERE seeker_user_id = ? AND status = ?
                   ORDER BY created_at DESC LIMIT 100""",
                (seeker, status),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM applications
                   WHERE seeker_user_id = ?
                   ORDER BY created_at DESC LIMIT 100""",
                (seeker,),
            ).fetchall()
    apps = [_row_to_app(r) for r in rows]
    return jsonify(applications=apps, total=len(apps))


@application_bp.route("/application/<application_id>", methods=["GET"])
@require_auth
def get_application(application_id: str):
    db = _db()
    viewer = str(g.user_id)
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
        if not row:
            return jsonify(error="not_found", message="投递记录不存在"), 404
        app = _row_to_app(row)
        is_seeker = app["seeker_user_id"] == viewer
        is_hr = _can_view_as_hr(conn, viewer, app["job_id"])
        if not is_seeker and not is_hr:
            return jsonify(error="forbidden", message="无权查看该投递"), 403

        payload = {"application": app}
        if is_hr:
            resume_row = conn.execute(
                "SELECT metadata FROM documents WHERE id = ? AND doc_type = 'resume'",
                (app["resume_id"],),
            ).fetchone()
            try:
                rmeta = json.loads((resume_row["metadata"] if resume_row else None) or "{}")
            except json.JSONDecodeError:
                rmeta = {}
            include_body = app["status"] == "submitted"
            payload["resume"] = _resume_payload_for_hr(rmeta, include_body=include_body)
        return jsonify(payload)


@application_bp.route("/application/<application_id>", methods=["DELETE"])
@require_auth
def withdraw_application(application_id: str):
    """Withdraw application — HR list/detail no longer expose resume body."""
    db = _db()
    seeker = str(g.user_id)
    now = _now_iso()
    with db.get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
        if not row:
            return jsonify(error="not_found", message="投递记录不存在"), 404
        if str(row["seeker_user_id"]) != seeker:
            return jsonify(error="forbidden", message="只能撤回自己的投递"), 403
        if row["status"] == "withdrawn":
            return jsonify(application=_row_to_app(row), already_withdrawn=True), 200

        conn.execute(
            """UPDATE applications
               SET status = 'withdrawn', withdrawn_at = ?, updated_at = ?
               WHERE id = ?""",
            (now, now, application_id),
        )
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (application_id,)
        ).fetchone()

    logger.info("application withdrawn id=%s seeker=%s", application_id, seeker)
    return jsonify(application=_row_to_app(row), already_withdrawn=False)


@application_bp.route("/jobs/<job_id>/applications", methods=["GET"])
@require_auth
def list_job_applications(job_id: str):
    """HR: list active (submitted) applications for a job, with resume summary."""
    viewer = str(g.user_id)
    db = _db()
    include_withdrawn = (request.args.get("include_withdrawn") or "").lower() in (
        "1",
        "true",
        "yes",
    )

    with db.get_conn() as conn:
        if not _can_view_as_hr(conn, viewer, job_id):
            # Job owner missing (e.g. mock id) — still allow admin/hr; else 403
            return jsonify(
                error="forbidden",
                message="无权查看该职位投递（需为职位发布者或 admin/hr）",
            ), 403

        if include_withdrawn:
            rows = conn.execute(
                """SELECT * FROM applications WHERE job_id = ?
                   ORDER BY created_at DESC LIMIT 200""",
                (job_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM applications
                   WHERE job_id = ? AND status = 'submitted'
                   ORDER BY created_at DESC LIMIT 200""",
                (job_id,),
            ).fetchall()

        items = []
        for r in rows:
            app = _row_to_app(r)
            resume_row = conn.execute(
                "SELECT title, metadata FROM documents WHERE id = ? AND doc_type = 'resume'",
                (app["resume_id"],),
            ).fetchone()
            try:
                rmeta = json.loads((resume_row["metadata"] if resume_row else None) or "{}")
            except json.JSONDecodeError:
                rmeta = {}
            include_body = app["status"] == "submitted"
            items.append({
                "application": app,
                "resume": _resume_payload_for_hr(rmeta, include_body=include_body),
                "resume_title": (resume_row["title"] if resume_row else ""),
            })

    return jsonify(job_id=job_id, applications=items, total=len(items))
