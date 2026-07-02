#!/usr/bin/env python3
"""
Standalone JWT verification for MCP Sidecar.
No Flask dependencies — reads secrets directly from environment.
"""
from __future__ import annotations

import logging
import os

import jwt as pyjwt

logger = logging.getLogger("looma.mcp.auth")


class MCPAuthError(Exception):
    """Raised when MCP token verification fails."""


class MCPForbiddenError(MCPAuthError):
    """Raised when user tier is insufficient."""


def _get_jwt_config() -> dict[str, str]:
    """Read JWT config from env (mirrors backend/src/config.py defaults)."""
    return {
        "secret": os.getenv(
            "JWT_SECRET",
            "looma-zervi-default-jwt-secret-change-in-production-2026",
        ),
        "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
    }


def verify_bearer_token(token: str) -> dict:
    """
    Verify a looma JWT bearer token.

    Returns the decoded payload dict containing at least {"sub": user_id, "tier": str}.

    Raises:
        MCPAuthError: invalid or missing token
    """
    if not token or not token.strip():
        raise MCPAuthError("Missing authentication token")

    cfg = _get_jwt_config()
    try:
        payload = pyjwt.decode(
            token.strip(),
            cfg["secret"],
            algorithms=[cfg["algorithm"]],
            issuer="looma",
        )
    except pyjwt.ExpiredSignatureError:
        raise MCPAuthError("Token has expired")
    except pyjwt.InvalidTokenError as e:
        raise MCPAuthError(f"Invalid token: {e}")

    if "sub" not in payload:
        raise MCPAuthError("Token missing 'sub' field")

    return payload


def verify_bearer_token_inline(
    token: str,
    user_id: str | None = None,
) -> dict:
    """
    Convenience wrapper: verify token, optionally check user_id consistency.

    Returns the decoded payload.

    Raises:
        MCPAuthError: verification failed
    """
    payload = verify_bearer_token(token)

    # If caller provides a user_id, validate it matches the token
    if user_id and payload["sub"] != user_id:
        raise MCPAuthError(
            f"Token subject ({payload['sub']}) does not match user_id ({user_id})"
        )

    return payload