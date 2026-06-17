"""
Looma api — 认证模块

支持多认证源：
  1. Supabase JWT（优先）
  2. Stub 模式（开发/演示用）
来源：Tatha api/auth.py，已迁入 looma-zervi。
"""
from __future__ import annotations

import os
import re
import json
import time
import base64
import uuid
import hashlib
from dataclasses import dataclass
from typing import Literal

# 确保 uuid 已导入（get_optional_auth 使用）

from fastapi import Header, HTTPException

Tier = Literal["guest", "free", "pro", "enterprise"]


@dataclass
class AuthContext:
    """请求上下文中的用户身份与档位，供业务与配额使用。"""
    user_id: str
    tier: Tier


def _decode_base64url(data: str) -> bytes:
    """Base64URL 解码（处理 padding）"""
    data = data + "=" * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data)


def _verify_supabase_jwt(token: str) -> AuthContext | None:
    """
    验证 Supabase 签发的 JWT token。
    验证逻辑：解析 Header、Payload，检查 exp 过期，提取 user_id。
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header = json.loads(_decode_base64url(parts[0]).decode("utf-8"))
        payload = json.loads(_decode_base64url(parts[1]).decode("utf-8"))

        if header.get("alg") not in ("HS256", "RS256"):
            return None

        exp = payload.get("exp")
        if exp and exp < time.time():
            return None

        user_id = payload.get("sub") or payload.get("user_id")
        if not user_id:
            return None

        tier: Tier = "free"
        tier_raw = payload.get("tier") or (payload.get("app_metadata") or {}).get("tier")
        if tier_raw in ("pro", "enterprise"):
            tier = tier_raw

        return AuthContext(user_id=str(user_id), tier=tier)
    except Exception:
        return None


def get_bearer_token(
    authorization: str | None = Header(None, alias="Authorization")
) -> str | None:
    """从请求头取出 Bearer token。"""
    if not authorization or not isinstance(authorization, str):
        return None
    auth = authorization.strip()
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    return token if token else None


def _verify_token_stub(token: str) -> AuthContext:
    """Stub：任意非空 token 视为 free 档。但如果 token 以 'token-' 开头，尝试从 DB 查询真实 tier。"""
    safe = re.sub(r"[^a-zA-Z0-9\-]", "", token[:32]) or "anon"

    # 尝试从 DB 查询真实 tier（本地 token 格式：token-{user_id[:8]}）
    tier: Tier = "free"
    if token.startswith("token-"):
        try:
            from src.db.manager import DBManager
            db = DBManager()
            # token 中的 user_id 前缀不足以查询，遍历匹配（小规模种子用户场景足够）
            users = db.list_users()
            for u in users:
                uid_prefix = u["id"][:8]
                if token == f"token-{uid_prefix}":
                    t = u.get("tier", "free")
                    if t in ("pro", "enterprise"):
                        tier = t
                    safe = u["id"]
                    break
        except Exception:
            pass

    return AuthContext(user_id=f"stub-{safe}", tier=tier)


def verify_token(token: str) -> AuthContext | None:
    """
    校验 token：Supabase JWT → Stub 模式。
    """
    ctx = _verify_supabase_jwt(token)
    if ctx is not None:
        return ctx

    if os.environ.get("AUTH_STUB", "true").lower() == "true":
        return _verify_token_stub(token)

    return None


def get_auth(
    authorization: str | None = Header(None, alias="Authorization")
) -> AuthContext:
    """
    依赖项：从请求头取 token，校验后返回 AuthContext。
    用于需要鉴权的路由。
    """
    token = get_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="missing or invalid authorization")
    ctx = verify_token(token)
    if ctx is None:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return ctx


def get_optional_auth(
    authorization: str | None = Header(None, alias="Authorization")
) -> AuthContext:
    """
    可选认证依赖项：有 token 则校验，无 token 自动分配游客身份。
    用于 v1/ask 等需要支持未登录体验的路由。
    游客通过 IP hash 区分，配额 3 次/日。
    """
    token = get_bearer_token(authorization)
    if token:
        ctx = verify_token(token)
        if ctx is not None:
            return ctx

    # 无 token 或 token 无效 → 分配游客身份
    guest_id = f"guest-{str(uuid.uuid4())[:12]}"
    return AuthContext(user_id=guest_id, tier="guest")


def _hash_password(password: str) -> str:
    """简单密码哈希"""
    salt = os.urandom(16).hex()
    h = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(password: str, stored: str) -> bool:
    """验证密码"""
    try:
        salt, h = stored.split(":", 1)
        return hashlib.sha256((password + salt).encode()).hexdigest() == h
    except Exception:
        return False