"""Looma api — 认证路由（注册/登录/刷新/配额）"""
from __future__ import annotations

import uuid
import hashlib
import os

from fastapi import APIRouter, Depends, HTTPException

from src.api.models import (
    AuthRegisterRequest, AuthLoginRequest, AuthResponse,
    QuotaResponse, QuotaRecord, Tier,
)
from src.api.auth import AuthContext, get_auth, _hash_password, verify_password
from src.api.quota import get_remaining, QUOTA_LIMITS, RESOURCE_ASK, RESOURCE_JOB_MATCH, RESOURCE_RAG, RESOURCE_RESUME_PARSE

router = APIRouter(tags=["auth"])


@router.post("/v1/auth/register", response_model=AuthResponse)
def auth_register(request: AuthRegisterRequest):
    """用户注册"""
    user_id = str(uuid.uuid4())
    password_hash = _hash_password(request.password)

    try:
        from src.db.manager import DBManager
        db = DBManager()
        existing = db.get_user_by_email(request.email)
        if existing:
            raise HTTPException(status_code=409, detail={"error": "email_exists", "message": "邮箱已注册"})
        db.create_user(user_id, request.email, password_hash)
    except HTTPException:
        raise
    except Exception:
        pass  # 回退：无 DB 时使用演示 token

    # 演示 token
    token = f"demo-token-{user_id[:8]}"
    return AuthResponse(
        access_token=token,
        refresh_token=f"refresh-{token}",
        tier=Tier.free,
        expires_in=3600,
        user_id=user_id,
    )


@router.post("/v1/auth/login", response_model=AuthResponse)
def auth_login(request: AuthLoginRequest):
    """用户登录"""
    try:
        from src.db.manager import DBManager
        db = DBManager()
        user = db.get_user_by_email(request.email)
        if not user or not verify_password(request.password, user["password_hash"]):
            # Stub 模式：任意凭据都能登录
            if os.environ.get("AUTH_STUB", "true").lower() == "true":
                uid = str(uuid.uuid4())
                token = f"demo-token-{uid[:8]}"
                return AuthResponse(
                    access_token=token,
                    refresh_token=f"refresh-{token}",
                    tier=Tier.free,
                    expires_in=3600,
                    user_id=uid,
                )
            raise HTTPException(status_code=401, detail={"error": "invalid_credentials", "message": "邮箱或密码错误"})
        token = f"token-{user['id'][:8]}"
        return AuthResponse(
            access_token=token,
            refresh_token=f"refresh-{token}",
            tier=Tier(user.get("tier", "free")),
            expires_in=3600,
            user_id=user["id"],
        )
    except HTTPException:
        raise
    except Exception:
        # 演示回退
        token = f"demo-token-{str(uuid.uuid4())[:8]}"
        return AuthResponse(
            access_token=token,
            refresh_token=f"refresh-{token}",
            tier=Tier.free,
            expires_in=3600,
            user_id=str(uuid.uuid4()),
        )


@router.get("/v1/quota", response_model=QuotaResponse)
def quota(auth: AuthContext = Depends(get_auth)):
    """查询配额使用情况"""
    records = []
    for resource, limit in QUOTA_LIMITS.get(auth.tier, QUOTA_LIMITS["free"]).items():
        remaining = get_remaining(auth.user_id, auth.tier, resource)
        used = limit - remaining
        records.append(QuotaRecord(
            resource=resource,
            used=used,
            daily_limit=limit,
        ))
    return QuotaResponse(tier=Tier(auth.tier), records=records)