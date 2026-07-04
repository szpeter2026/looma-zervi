"""
Payment routes blueprint — Stub provider for internal testing.
Ownership: JOINT

Endpoints:
  GET  /v1/payment/plans    - List available pricing plans (region-aware)
  GET  /v1/payment/status   - Current user's subscription status
  POST /v1/payment/upgrade  - Upgrade tier (stub: no real payment)

Pricing contract: backend/contracts/payment.v1.json
  CN supporter: ¥9.9/mo · US supporter: $1.99/mo

For production, replace stub logic with WeChat Pay / Stripe integration.
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
from src.payment.plans import get_plan_for_tier, list_plans_for_region, resolve_region

payment_bp = Blueprint("payment", __name__)

UPGRADABLE_TIERS = frozenset({"supporter", "pro"})
TIER_ORDER = {"free": 0, "supporter": 1, "pro": 2, "enterprise": 3}


@payment_bp.route("/payment/plans", methods=["GET"])
def list_plans():
    """List pricing plans for a billing region (?region=CN|US)."""
    region = resolve_region(
        request.args.get("region"),
        request.headers.get("Accept-Language"),
    )
    return jsonify(**list_plans_for_region(region))


@payment_bp.route("/payment/status", methods=["GET"])
@require_auth
def payment_status():
    """Get current user's subscription status."""
    region = resolve_region(
        request.args.get("region"),
        request.headers.get("Accept-Language"),
    )
    tier = g.get("user_tier", "free")
    if tier == "enterprise":
        plan = {
            "tier": "enterprise",
            "name": "企业版" if region == "CN" else "Enterprise",
            "price_monthly": 0,
            "currency": list_plans_for_region(region)["currency"],
            "region": region,
            "plan_id": f"enterprise_contact_{region.lower()}",
            "features": [],
            "upgradable": False,
        }
    else:
        try:
            plan = get_plan_for_tier(tier, region)
        except KeyError:
            plan = get_plan_for_tier("free", region)
    return jsonify(
        tier=tier,
        plan=plan,
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

    if new_tier not in UPGRADABLE_TIERS:
        return jsonify(error="bad_request", message="Invalid tier. Choose: supporter, pro"), 400

    current_tier = g.get("user_tier", "free")

    if TIER_ORDER.get(new_tier, 0) <= TIER_ORDER.get(current_tier, 0):
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

    region = resolve_region(
        request.args.get("region") or data.get("region"),
        request.headers.get("Accept-Language"),
    )
    plan = get_plan_for_tier(new_tier, region)
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
