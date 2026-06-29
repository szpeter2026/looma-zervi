"""
JWT token signing and verification.
Replaces the old AUTH_STUB mechanism with real JWT.
"""
import jwt
import time
from flask import current_app, g


def sign_token(user_id: str, extra_claims: dict = None) -> str:
    """
    Sign a looma JWT for the given user_id.
    Returns a compact JWT string.
    """
    config = current_app.config
    now = int(time.time())
    payload = {
        "sub": user_id,           # subject = looma user_id
        "iat": now,               # issued at
        "exp": now + config["JWT_EXPIRY_HOURS"] * 3600,
        "iss": "looma",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, config["JWT_SECRET"], algorithm=config["JWT_ALGORITHM"])


def verify_token(token: str) -> dict:
    """
    Verify a looma JWT.
    Returns the decoded payload dict if valid.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    config = current_app.config
    return jwt.decode(
        token,
        config["JWT_SECRET"],
        algorithms=[config["JWT_ALGORITHM"]],
        issuer="looma",
    )


def get_current_user_id() -> str:
    """Get the authenticated user_id from request context (set by @require_auth)."""
    return g.get("user_id")


def get_current_user_tier() -> str:
    """Get the authenticated user's tier from request context."""
    return g.get("user_tier", "free")
