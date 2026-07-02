"""
Payment routes blueprint — Stub provider for internal testing.
Ownership: JOINT

Endpoints:
  GET  /v1/payment/plans    - List available pricing plans
  GET  /v1/payment/status   - Current user's subscription status
  POST /v1/payment/upgrade  - Upgrade tier (stub: no real payment)

For production, replace stub logic with WeChat Pay / Alipay integration.
"""
from flask import Blueprint, jsonify, g, request, current_app

from src.api.auth.decorators import require_auth
from src.api.auth.jwt_handler import sign_token_for_user
from src.analytics.events import (
    log_product_event,
    platform_from_request,
    EVENT_TRIAL_STARTED,
    EVENT_TRIAL_FAILED,
)

payment_bp = Blueprint("payment", __name__)

# --- Pricing plans (hardcoded for MVP) ---
PLANS = {
    "free": {
        "tier": "free",
        "name": "免费版",
        "price_monthly": 0,
        "features": [
            "每日 30 次 AI 对话",
            "基础岗位匹配",
            "简历解析（3次/天）",
        ],
    },
    "supporter": {
        "tier": "supporter",
        "name": "支持者版",
        "price_monthly": 9.9,
        "features": [
            "每日 100 次 AI 对话",
            "高级岗位匹配",
            "简历解析（不限）",
            "专属星球徽章",
        ],
    },
    "pro": {
        "tier": "pro",
        "name": "专业版",
        "price_monthly": 29.9,
        "features": [
            "AI 对话不限",
            "全功能岗位匹配",
            "简历解析（不限）",
            "企业级报告",
            "优先客服",
        ],
    },
}


@payment_bp.route("/payment/plans", methods=["GET"])
def list_plans():
    """List all available pricing plans."""
    return jsonify(plans=list(PLANS.values()))


@payment_bp.route("/payment/status", methods=["GET"])
@require_auth
def payment_status():
    """Get current user's subscription status."""
    tier = g.get("user_tier", "free")
    plan = PLANS.get(tier, PLANS["free"])
    return jsonify(
        tier=tier,
        plan=plan,
        # Stub: always show as active for internal testing
        status="active",
        expires_at=None,
    )


@payment_bp.route("/payment/upgrade", methods=["POST"])
@require_auth
def upgrade_tier():
    """Upgrade user tier — stub mode (no real payment).

    Request body:
        { "tier": "supporter" | "pro" }
    """
    data = request.get_json(silent=True) or {}
    new_tier = data.get("tier")

    if new_tier not in ("supporter", "pro"):
        return jsonify(error="bad_request", message="Invalid tier. Choose: supporter, pro"), 400

    current_tier = g.get("user_tier", "free")

    # Tier downgrade not allowed via this endpoint
    tier_order = {"free": 0, "supporter": 1, "pro": 2}
    if tier_order.get(new_tier, 0) <= tier_order.get(current_tier, 0):
        log_product_event(
            current_app._db,
            EVENT_TRIAL_FAILED,
            user_id=g.user_id,
            platform=platform_from_request(request),
            source="server",
            success=False,
            properties={"reason": "downgrade", "current_tier": current_tier, "requested": new_tier},
        )
        return jsonify(
            error="bad_request",
            message=f"Cannot downgrade from {current_tier} to {new_tier}",
        ), 400

    # --- Stub: directly update tier in DB (no payment) ---
    db = current_app._db
    db.update_user_tier(g.user_id, new_tier)

    if new_tier == "pro":
        log_product_event(
            db,
            EVENT_TRIAL_STARTED,
            user_id=g.user_id,
            platform=platform_from_request(request),
            source="server",
            properties={"from_tier": current_tier},
        )

    plan = PLANS[new_tier]
    access_token = sign_token_for_user(db, g.user_id)
    return jsonify(
        tier=new_tier,
        plan=plan,
        status="active",
        access_token=access_token,
        token_type="bearer",
        expires_in=current_app.config["JWT_EXPIRY_HOURS"] * 3600,
        message="[STUB] Tier upgraded without real payment. Replace with WeChat Pay for production.",
    )
