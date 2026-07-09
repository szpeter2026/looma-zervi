"""
Authentication decorators for route protection.
Replaces the old AUTH_STUB with real JWT verification.
"""
from functools import wraps
from flask import request, jsonify, g, current_app
from src.api.auth.jwt_handler import verify_token


def require_auth(f):
    """
    Require a valid looma JWT in the Authorization header.
    Verifies token, loads user from DB, sets g.user_id / g.user_tier / g.user_role.
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

        user_id = payload["sub"]
        db = getattr(current_app, "_db", None)
        if db is None:
            return jsonify(error="server_error", message="database unavailable"), 500

        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify(error="unauthorized", message="user not found"), 401

        g.user_id = user_id
        g.user_tier = user.get("tier", "free")
        g.user_role = user.get("role", "user")
        return f(*args, **kwargs)

    return decorated


def require_tier(min_tier: str):
    """
    Require the user to have at least the given tier.
    Tier hierarchy: guest < free < supporter < pro < enterprise
    Usage: @require_auth @require_tier("pro")
    """
    tier_order = {"guest": -1, "free": 0, "supporter": 1, "pro": 2, "enterprise": 3}

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


def optional_auth(f):
    """
    Optional auth — if token is present, set g.user_id/g.user_tier;
    if absent, treat as guest with a random ID.
    Used by /v1/ask where guest users also have limited quota.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = verify_token(token)
            except Exception:
                pass  # Invalid token → fall through to guest
            else:
                g.user_id = payload["sub"]
                g.user_tier = payload.get("tier", "free")
                return f(*args, **kwargs)

        import uuid
        g.user_id = f"guest-{str(uuid.uuid4())[:12]}"
        g.user_tier = "guest"
        return f(*args, **kwargs)

    return decorated
