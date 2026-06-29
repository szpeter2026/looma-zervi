"""
Quota management utilities.
Checks and enforces daily usage limits per tier.
"""
from flask import current_app, g


def check_quota() -> tuple:
    """
    Check if the current user has remaining quota.

    Returns:
        (allowed: bool, remaining: int, limit: int)
    """
    tier = g.get("user_tier", "free")

    if tier in ("supporter", "pro"):
        return (True, 999999, 999999)

    db = current_app._db
    used = db.get_daily_usage_count(g.user_id)
    limit = current_app.config["FREE_DAILY_LIMIT"]
    remaining = max(0, limit - used)

    return (remaining > 0, remaining, limit)


def consume_quota(endpoint: str, tokens_used: int = 0):
    """Log a usage event for the current user."""
    db = current_app._db
    db.log_usage(g.user_id, endpoint, tokens_used)
