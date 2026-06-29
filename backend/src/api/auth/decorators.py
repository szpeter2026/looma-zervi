"""
Authentication decorators for route protection.
Replaces the old AUTH_STUB with real JWT verification.
"""
from functools import wraps
from flask import request, jsonify, g
from src.api.auth.jwt_handler import verify_token


def require_auth(f):
    """
    Require a valid looma JWT in the Authorization header.
    Sets g.user_id and g.user_tier for the handler.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify(error="unauthorized", message="Missing or invalid Authorization header"), 401

        token = auth_header[7:]  # strip "Bearer "
        try:
            payload = verify_token(token)
        except Exception as e:
            return jsonify(error="unauthorized", message=f"Invalid token: {str(e)}"), 401

        g.user_id = payload["sub"]
        g.user_tier = payload.get("tier", "free")
        return f(*args, **kwargs)

    return decorated


def require_tier(min_tier: str):
    """
    Require the user to have at least the given tier.
    Tier hierarchy: free < supporter < pro
    Usage: @require_auth @require_tier("pro")
    """
    tier_order = {"free": 0, "supporter": 1, "pro": 2}

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_tier = g.get("user_tier", "free")
            if tier_order.get(user_tier, 0) < tier_order.get(min_tier, 0):
                return jsonify(
                    error="forbidden",
                    message=f"Requires tier '{min_tier}' or above"
                ), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
