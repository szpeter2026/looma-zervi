"""
Match report persistence — save resume×JD match results for later review.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from src.compliance.redact import redact_pii

logger = logging.getLogger("looma.match_reports")

PIPELINE_VERSION = "job_match_v2"


def _now_iso() -> str:
    return datetime.now().isoformat()


def _json_dumps(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def _json_loads(raw: str | None, default: Any = None) -> Any:
    if default is None:
        default = []
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default


class MatchReportManager:
    """CRUD for match_reports / match_report_items."""

    def __init__(self, db):
        self.db = db

    def create_report(
        self,
        user_id: str,
        resume_text: str,
        matches: list[dict],
        title: str = "",
        summary: str = "",
        resume_id: str = "",
    ) -> dict:
        if not matches:
            raise ValueError("matches_required")

        safe_resume, _ = redact_pii(resume_text or "")
        report_id = str(uuid.uuid4())
        now = _now_iso()
        scores = [
            float((m.get("scores") or {}).get("overall") or m.get("overall_score") or 0)
            for m in matches
        ]
        meta = {
            "total_jobs": len(matches),
            "matched_at": now,
            "pipeline_version": PIPELINE_VERSION,
            "max_score": max(scores) if scores else 0,
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        }
        if not title:
            title = f"{now[:10]} 求职匹配报告"
        if not summary:
            summary = (
                f"共匹配 {len(matches)} 个职位，最高分 {meta['max_score']}，"
                f"平均分 {meta['avg_score']}。"
            )

        with self.db.get_conn() as conn:
            conn.execute(
                """INSERT INTO match_reports
                   (id, user_id, resume_id, resume_snapshot, title, status, summary, metadata, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, 'completed', ?, ?, ?, ?)""",
                (
                    report_id,
                    user_id,
                    resume_id or "",
                    safe_resume[:8000],
                    title[:120],
                    summary[:1000],
                    json.dumps(meta, ensure_ascii=False),
                    now,
                    now,
                ),
            )
            for idx, match in enumerate(matches):
                self._insert_item(conn, report_id, match, idx, now)

        return self.get_report(report_id, user_id=user_id)  # type: ignore[return-value]

    def _insert_item(self, conn, report_id: str, match: dict, rank: int, now: str) -> None:
        scores = match.get("scores") or {}
        item_id = str(uuid.uuid4())
        gap = match.get("gap_analysis") or scores.get("gap_analysis") or []
        missing = match.get("missing_skills") or scores.get("missing_skills") or []
        plan = match.get("improvement_plan") or scores.get("improvement_plan") or ""
        credit = match.get("credit_snapshot") or {}

        conn.execute(
            """INSERT INTO match_report_items (
                id, report_id, job_title, company_name, location, salary_range, jd_snapshot,
                overall_score, background_match, skills_overlap, experience_relevance,
                seniority, language_requirement, company_score, salary_match,
                location_match, culture_workload_match,
                match_reason, matched_skills, missing_skills, fit_bullets,
                gap_analysis, improvement_plan, credit_snapshot, rank_order, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                item_id,
                report_id,
                str(match.get("title") or match.get("job_title") or "未命名职位")[:200],
                str(match.get("company") or match.get("company_name") or "未知公司")[:200],
                str(match.get("location") or "")[:120],
                str(match.get("salary_range") or "")[:120],
                str(match.get("jd_snapshot") or match.get("description") or "")[:4000],
                float(scores.get("overall") or match.get("overall_score") or 0),
                float(scores.get("background_match") or 0),
                float(scores.get("skills_overlap") or 0),
                float(scores.get("experience_relevance") or 0),
                float(scores.get("seniority") or 0),
                float(scores.get("language_requirement") or 0),
                float(scores.get("company_score") or 0),
                float(scores.get("salary_match") or 0),
                float(scores.get("location_match") or 0),
                float(scores.get("culture_workload_match") or 0),
                str(match.get("reason") or scores.get("summary") or "")[:500],
                _json_dumps(match.get("matched_skills") or scores.get("keywords") or []),
                _json_dumps(missing),
                _json_dumps(match.get("fit_bullets") or scores.get("fit_bullets") or []),
                _json_dumps(gap),
                str(plan)[:2000],
                _json_dumps(credit if isinstance(credit, dict) else {}),
                rank,
                now,
            ),
        )

    def list_user_reports(self, user_id: str, page: int = 1, page_size: int = 20) -> dict:
        page = max(1, page)
        page_size = min(max(1, page_size), 50)
        offset = (page - 1) * page_size
        with self.db.get_conn() as conn:
            total = conn.execute(
                "SELECT COUNT(*) AS c FROM match_reports WHERE user_id=? AND status!='deleted'",
                (user_id,),
            ).fetchone()["c"]
            rows = conn.execute(
                """SELECT id, user_id, title, status, summary, metadata, created_at, updated_at
                   FROM match_reports
                   WHERE user_id=? AND status!='deleted'
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?""",
                (user_id, page_size, offset),
            ).fetchall()
        reports = [self._row_to_summary(dict(r)) for r in rows]
        return {"reports": reports, "total": total, "page": page, "page_size": page_size}

    def get_report(self, report_id: str, user_id: str | None = None) -> dict | None:
        with self.db.get_conn() as conn:
            if user_id:
                row = conn.execute(
                    """SELECT * FROM match_reports
                       WHERE id=? AND user_id=? AND status!='deleted'""",
                    (report_id, user_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM match_reports WHERE id=? AND status!='deleted'",
                    (report_id,),
                ).fetchone()
            if not row:
                return None
            items = conn.execute(
                """SELECT * FROM match_report_items
                   WHERE report_id=? ORDER BY rank_order ASC, overall_score DESC""",
                (report_id,),
            ).fetchall()
        report = self._row_to_summary(dict(row))
        report["resume_snapshot"] = row["resume_snapshot"] or ""
        report["resume_id"] = row["resume_id"] or ""
        report["items"] = [self._item_to_dict(dict(i)) for i in items]
        return report

    def delete_report(self, report_id: str, user_id: str) -> bool:
        now = _now_iso()
        with self.db.get_conn() as conn:
            cur = conn.execute(
                """UPDATE match_reports
                   SET status='deleted', updated_at=?
                   WHERE id=? AND user_id=? AND status!='deleted'""",
                (now, report_id, user_id),
            )
            return cur.rowcount > 0

    def _row_to_summary(self, row: dict) -> dict:
        meta = _json_loads(row.get("metadata"), {})
        if not isinstance(meta, dict):
            meta = {}
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "title": row.get("title") or "",
            "status": row.get("status") or "completed",
            "summary": row.get("summary") or "",
            "metadata": meta,
            "created_at": row.get("created_at") or "",
            "updated_at": row.get("updated_at") or "",
        }

    def _item_to_dict(self, row: dict) -> dict:
        return {
            "id": row["id"],
            "report_id": row["report_id"],
            "job_title": row["job_title"],
            "company_name": row["company_name"],
            "location": row.get("location") or "",
            "salary_range": row.get("salary_range") or "",
            "overall_score": row.get("overall_score") or 0,
            "background_match": row.get("background_match") or 0,
            "skills_overlap": row.get("skills_overlap") or 0,
            "experience_relevance": row.get("experience_relevance") or 0,
            "seniority": row.get("seniority") or 0,
            "language_requirement": row.get("language_requirement") or 0,
            "company_score": row.get("company_score") or 0,
            "salary_match": row.get("salary_match") or 0,
            "location_match": row.get("location_match") or 0,
            "culture_workload_match": row.get("culture_workload_match") or 0,
            "match_reason": row.get("match_reason") or "",
            "matched_skills": _json_loads(row.get("matched_skills"), []),
            "missing_skills": _json_loads(row.get("missing_skills"), []),
            "fit_bullets": _json_loads(row.get("fit_bullets"), []),
            "gap_analysis": _json_loads(row.get("gap_analysis"), []),
            "improvement_plan": row.get("improvement_plan") or "",
            "credit_snapshot": _json_loads(row.get("credit_snapshot"), {}),
            "rank_order": row.get("rank_order") or 0,
            "created_at": row.get("created_at") or "",
        }
