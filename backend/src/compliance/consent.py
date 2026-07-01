"""
Compliance Gate: Consent verification.
PIPL 合规：单独同意 / 目的限定 / 可撤回
"""
from __future__ import annotations

import functools
import logging
import uuid
from datetime import datetime
from typing import Callable

from flask import g, current_app, request, jsonify

logger = logging.getLogger("looma.compliance.consent")

ALL_SCOPES = frozenset({
    "resume_upload", "resume_parse", "credit_query", "credit_analyze",
    "profile_share", "ask_rag", "job_match", "mbti_analyze", "navigator_memory",
})


def _now_iso():
    return datetime.now().isoformat()


class ConsentManager:
    def __init__(self, db=None):
        self._db = db

    @property
    def db(self):
        if self._db is not None:
            return self._db
        return getattr(current_app, "_db", None) or getattr(g, "_db", None)

    def grant(self, user_id, scope, ip="", user_agent="", purpose=""):
        if scope not in ALL_SCOPES:
            raise ValueError(f"Unknown consent scope: {scope}")
        cid = str(uuid.uuid4())
        now = _now_iso()
        db = self.db
        if db is None:
            raise RuntimeError("No database available")
        with db.get_conn() as conn:
            ex = conn.execute(
                "SELECT id FROM consents WHERE user_id=? AND scope=? AND status='granted'",
                (user_id, scope),
            ).fetchone()
            if ex:
                return {"consent_id": ex["id"], "already_granted": True}
            conn.execute(
                """INSERT INTO consents
                   (id, user_id, scope, purpose, status, ip, user_agent,
                    granted_at, created_at, updated_at)
                   VALUES (?,?,?,?,'granted',?,?,?,?,?)""",
                (cid, user_id, scope, purpose or scope, ip, user_agent, now, now, now),
            )
        return {"consent_id": cid, "already_granted": False}

    def revoke(self, user_id, scope):
        db = self.db
        if db is None:
            raise RuntimeError("No database available")
        now = _now_iso()
        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM consents WHERE user_id=? AND scope=? AND status='granted'",
                (user_id, scope),
            ).fetchone()
            if not row:
                return {"revoked": False, "reason": "No active consent found"}
            conn.execute(
                "UPDATE consents SET status='revoked', revoked_at=?, updated_at=? WHERE id=?",
                (now, now, row["id"]),
            )
        return {"revoked": True, "consent_id": row["id"]}

    def check(self, user_id, scope):
        if scope not in ALL_SCOPES:
            return False
        db = self.db
        if db is None:
            return False
        with db.get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM consents WHERE user_id=? AND scope=? AND status='granted'",
                (user_id, scope),
            ).fetchone()
        return row is not None

    def get_user_consents(self, user_id):
        db = self.db
        if db is None:
            return []
        with db.get_conn() as conn:
            rows = conn.execute(
                "SELECT id, scope, purpose, status, granted_at, revoked_at "
                "FROM consents WHERE user_id=? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def grant_batch(self, user_id, scopes, ip="", user_agent=""):
        results = []
        for scope in scopes:
            try:
                r = self.grant(user_id, scope, ip=ip, user_agent=user_agent)
                results.append({"scope": scope, **r})
            except Exception as e:
                results.append({"scope": scope, "error": str(e)})
        return {"granted": len([r for r in results if "error" not in r]), "results": results}

    def has_any(self, user_id, scopes):
        return any(self.check(user_id, s) for s in scopes)

    def has_all(self, user_id, scopes):
        return all(self.check(user_id, s) for s in scopes)


_cm = None

def get_consent_manager(db=None):
    global _cm
    if _cm is None:
        _cm = ConsentManager(db=db)
    elif db is not None and _cm._db is None:
        _cm._db = db
    return _cm

def reset_consent_manager():
    global _cm
    _cm = None

def require_consent(scope, extract_user_id=None):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            uid = None
            if extract_user_id:
                uid = extract_user_id()
            else:
                uid = kwargs.get("user_id") or getattr(g, "user_id", None)
            if not uid:
                return jsonify(error="consent_required",
                               message=f"需要授权: {scope}", required_scope=scope), 403
            c = get_consent_manager()
            if not c.check(uid, scope):
                return jsonify(error="consent_required",
                               message=f"需要授权: {scope}", required_scope=scope,
                               action="grant_consent"), 403
            g.compliance_scope = scope
            g.compliance_user_id = uid
            return fn(*args, **kwargs)
        return wrapper
    return decorator