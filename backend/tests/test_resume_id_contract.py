"""A1: resume_id must be documents.id; list/analysis/delete are owner-scoped."""
from __future__ import annotations

import json


def _register(client, email: str = "resume-a1@test.com"):
    resp = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123", "name": "Resume A1"},
    )
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()
    token = data["access_token"]
    user_id = data["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}
    return user_id, headers


def test_resume_id_roundtrip_list_analysis_delete(client, app):
    user_id, headers = _register(client)
    db = app._db

    with db.get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO documents (title, file_path, doc_type, file_size, metadata, status, created_at)
               VALUES (?, ?, 'resume', 1, ?, 'processed', datetime('now'))""",
            (
                "cv.pdf",
                f"resume/{user_id}/tmp.pdf",
                json.dumps(
                    {
                        "user_id": user_id,
                        "markdown": "Python Django 工程师",
                        "extracted": {"skills": ["Python"]},
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        rid = str(cur.lastrowid)
        conn.execute(
            "UPDATE documents SET file_path=? WHERE id=?",
            (f"resume/{user_id}/{rid}_cv.pdf", int(rid)),
        )

    listed = client.get("/v1/resume/list", headers=headers)
    assert listed.status_code == 200
    ids = {r["id"] for r in (listed.get_json() or {}).get("resumes") or []}
    assert rid in ids

    analysis = client.get(f"/v1/resume/analysis?resume_id={rid}", headers=headers)
    assert analysis.status_code != 404
    assert (analysis.get_json() or {}).get("resume_id") == rid

    deleted = client.delete(f"/v1/resume/{rid}", headers=headers)
    assert deleted.status_code == 200
    assert (deleted.get_json() or {}).get("resume_id") == rid

    gone = client.get(f"/v1/resume/analysis?resume_id={rid}", headers=headers)
    assert gone.status_code == 404


def test_resume_list_filters_by_owner(client, app):
    user_id, headers = _register(client, email="resume-a1-owner@test.com")
    db = app._db
    with db.get_conn() as conn:
        conn.execute(
            """INSERT INTO documents (title, file_path, doc_type, file_size, metadata, status, created_at)
               VALUES ('other.pdf', 'resume/other/9_other.pdf', 'resume', 1, ?, 'processed', datetime('now'))""",
            (json.dumps({"user_id": "someone-else", "markdown": "x"}, ensure_ascii=False),),
        )
        conn.execute(
            """INSERT INTO documents (title, file_path, doc_type, file_size, metadata, status, created_at)
               VALUES ('mine.pdf', ?, 'resume', 1, ?, 'processed', datetime('now'))""",
            (
                f"resume/{user_id}/1_mine.pdf",
                json.dumps({"user_id": user_id, "markdown": "mine"}, ensure_ascii=False),
            ),
        )

    listed = client.get("/v1/resume/list", headers=headers)
    assert listed.status_code == 200
    resumes = (listed.get_json() or {}).get("resumes") or []
    assert len(resumes) >= 1
    for r in resumes:
        assert "resume/other/" not in str(r.get("filename") or "")


def test_format_match_report_block_empty_and_present():
    from src.agents.central_brain import _format_match_report_block

    assert _format_match_report_block({}) == ""
    assert _format_match_report_block({"match_report": None}) == ""
    block = _format_match_report_block(
        {
            "match_report": {
                "report_id": "r1",
                "title": "测试报告",
                "resume_summary": "Python",
                "top_items": [
                    {
                        "job_title": "后端",
                        "overall_score": 90,
                        "matched_skills": ["Python"],
                        "missing_skills": ["Go"],
                        "gap_analysis": "缺 Go",
                    }
                ],
            }
        }
    )
    assert "当前匹配报告上下文" in block
    assert "后端" in block
    assert "缺 Go" in block
