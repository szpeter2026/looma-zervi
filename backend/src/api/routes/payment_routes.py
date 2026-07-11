"""
Payment routes blueprint — Stub provider for internal testing + WeChat Pay skeleton.

Endpoints:
  GET  /v1/payment/plans         - List available pricing plans (region-aware)
  GET  /v1/payment/status        - Current user's subscription status
  POST /v1/payment/upgrade       - Upgrade tier (stub: blocked unless PAYMENT_STUB_MODE=true)
  POST /v1/payment/wechat/order  - Create WeChat Pay order → prepay_id / qr_code
  POST /v1/payment/wechat/notify - WeChat Pay callback (no auth, signature verified)

Pricing contract: backend/contracts/payment.v1.json
  CN supporter: ¥9.9/mo · US supporter: $1.99/mo

For production, set PAYMENT_STUB_MODE=false and configure WeChat Pay credentials.
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
from src.payment.wechat_pay import (
    create_native_order,
    generate_out_trade_no,
    verify_notify_sign,
    parse_notify_body,
    build_notify_response,
    WECHAT_SIGNATURE_HEADER,
    WECHAT_SERIAL_HEADER,
    WECHAT_TIMESTAMP_HEADER,
    WECHAT_NONCE_HEADER,
)

payment_bp = Blueprint("payment", __name__)

UPGRADABLE_TIERS = frozenset({"supporter", "pro"})
TIER_ORDER = {"free": 0, "supporter": 1, "pro": 2, "enterprise": 3}

# 人民币金额 → 分（WeChat Pay 以分为单位）
TIER_PRICE_FEN = {
    "supporter": 990,   # ¥9.90
    "pro": 2990,         # ¥29.90
}


def _is_stub_mode():
    """检查当前是否为 Stub 模式。"""
    return current_app.config.get("PAYMENT_STUB_MODE", True)


@payment_bp.route("/payment/plans", methods=["GET"])
def list_plans():
    """List pricing plans for a billing region (?region=CN|US)."""
    region = resolve_region(
        request.args.get("region"),
        request.headers.get("Accept-Language"),
    )
    payload = list_plans_for_region(region)
    # 附加 stub_mode 标志，前端据此调整支付流程
    payload["stub_mode"] = _is_stub_mode()
    return jsonify(**payload)


@payment_bp.route("/payment/status", methods=["GET"])
@require_auth
def payment_status():
    """Get current user's subscription status, including real subscription expiry."""
    region = resolve_region(
        request.args.get("region"),
        request.headers.get("Accept-Language"),
    )
    tier = g.get("user_tier", "free")

    # 查询真实订阅信息
    db = current_app._db
    sub = db.get_subscription(g.user_id)
    expires_at = sub["expires_at"] if sub else None
    sub_status = sub["status"] if sub else ("active" if tier != "free" else "inactive")

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
        status=sub_status,
        expires_at=expires_at,
        stub_mode=_is_stub_mode(),
    )


@payment_bp.route("/payment/upgrade", methods=["POST"])
@require_auth
def upgrade_tier():
    """Upgrade user tier.

    - Stub mode (dev): direct tier upgrade, no payment required.
    - Production mode: **blocked** — must go through WeChat Pay / Stripe order flow.
    """
    if not _is_stub_mode():
        return jsonify(
            error="payment_required",
            message="Upgrade requires real payment. Please use POST /v1/payment/wechat/order to create a payment order.",
            hint="Set PAYMENT_STUB_MODE=true in development if you need a quick upgrade.",
        ), 402

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

    # 创建 Stub 订单记录（审计用）
    region = resolve_region(
        request.args.get("region") or data.get("region"),
        request.headers.get("Accept-Language"),
    )
    plan = get_plan_for_tier(new_tier, region)
    db.create_order(
        user_id=g.user_id,
        plan_id=plan["plan_id"],
        tier=new_tier,
        amount=plan["price_monthly"],
        currency=plan["currency"],
        out_trade_no=generate_out_trade_no(),
        metadata_json={"mode": "stub", "region": region},
    )

    if new_tier == "pro":
        log_product_event(
            db,
            EVENT_TRIAL_STARTED,
            user_id=g.user_id,
            platform=platform_from_request(request),
            source="server",
            properties={"from_tier": current_tier},
        )

    access_token = sign_token_for_user(db, g.user_id)
    return jsonify(
        tier=new_tier,
        plan=plan,
        status="active",
        access_token=access_token,
        token_type="bearer",
        expires_in=current_app.config["JWT_EXPIRY_HOURS"] * 3600,
        message="[STUB] Tier upgraded without real payment. Set PAYMENT_STUB_MODE=false for production.",
    )


# ============================================================
# WeChat Pay 路由
# ============================================================

@payment_bp.route("/payment/wechat/order", methods=["POST"])
@require_auth
def create_wechat_order():
    """创建 WeChat Pay 支付订单。

    根据用户环境选择支付方式：
      - PC Web：Native 支付 → 返回 qr_code_url，前端渲染二维码
      - 微信内：JSAPI 支付 → 返回 prepay_id + 签名，前端 wx.chooseWXPay

    Request body:
        { "tier": "supporter" | "pro", "trade_type": "NATIVE" | "JSAPI", "openid": "..." }

    Response:
        { "out_trade_no": "...", "prepay_id": "...", "qr_code_url": "...",
          "jsapi_params": { "appId": "...", "timeStamp": "...", ... } }
    """
    if _is_stub_mode():
        return jsonify(
            error="stub_mode",
            message="Payment stub mode is enabled. Use POST /v1/payment/upgrade for instant tier change, or set PAYMENT_STUB_MODE=false to enable real payments.",
        ), 400

    data = request.get_json(silent=True) or {}
    new_tier = data.get("tier")
    trade_type = data.get("trade_type", "NATIVE").upper()
    openid = data.get("openid", "")

    if new_tier not in UPGRADABLE_TIERS:
        return jsonify(error="bad_request", message="Invalid tier. Choose: supporter, pro"), 400

    current_tier = g.get("user_tier", "free")
    if TIER_ORDER.get(new_tier, 0) <= TIER_ORDER.get(current_tier, 0):
        return jsonify(
            error="bad_request",
            message=f"Cannot downgrade from {current_tier} to {new_tier}",
        ), 400

    if new_tier not in TIER_PRICE_FEN:
        return jsonify(error="bad_request", message=f"No price configured for tier: {new_tier}"), 400

    region = resolve_region(
        request.args.get("region"),
        request.headers.get("Accept-Language"),
    )
    plan = get_plan_for_tier(new_tier, region)

    # 从配置读取 WeChat Pay 凭证
    mchid = current_app.config.get("WECHAT_MCHID", "")
    appid = current_app.config.get("WECHAT_APPID", "")
    api_v3_key = current_app.config.get("WECHAT_API_V3_KEY", "")
    serial_no = current_app.config.get("WECHAT_SERIAL_NO", "")
    private_key_path = current_app.config.get("WECHAT_PRIVATE_KEY_PATH", "")
    notify_url = current_app.config.get("WECHAT_NOTIFY_URL", "")

    if not all([mchid, appid, api_v3_key, serial_no, notify_url]):
        return jsonify(
            error="payment_not_configured",
            message="WeChat Pay credentials not configured. Set WECHAT_MCHID, WECHAT_APPID, WECHAT_API_V3_KEY, WECHAT_SERIAL_NO, WECHAT_PRIVATE_KEY_PATH, WECHAT_NOTIFY_URL env vars.",
        ), 503

    amount_fen = TIER_PRICE_FEN[new_tier]
    out_trade_no = generate_out_trade_no()
    description = f"Looma {plan['name']}"

    if trade_type == "JSAPI" and openid:
        from src.payment.wechat_pay import create_jsapi_order
        result = create_jsapi_order(
            mchid=mchid, appid=appid, openid=openid,
            description=description, out_trade_no=out_trade_no,
            amount_total=amount_fen, notify_url=notify_url,
            api_v3_key=api_v3_key, serial_no=serial_no,
            private_key_path=private_key_path,
        )
        jsapi_params = {
            "appId": appid,
            "timeStamp": result.jsapi_time_stamp,
            "nonceStr": result.jsapi_nonce_str,
            "package": result.jsapi_package,
            "signType": "RSA",
            "paySign": result.jsapi_pay_sign,
        }
    else:
        # 默认 Native 支付
        result = create_native_order(
            mchid=mchid, appid=appid,
            description=description, out_trade_no=out_trade_no,
            amount_total=amount_fen, notify_url=notify_url,
            api_v3_key=api_v3_key, serial_no=serial_no,
            private_key_path=private_key_path,
        )
        jsapi_params = None

    # 写入订单表
    db = current_app._db
    order = db.create_order(
        user_id=g.user_id,
        plan_id=plan["plan_id"],
        tier=new_tier,
        amount=plan["price_monthly"],
        currency="CNY",
        out_trade_no=out_trade_no,
        prepay_id=result.prepay_id,
        qr_code_url=result.qr_code_url,
        metadata_json={
            "trade_type": trade_type,
            "region": region,
        },
    )

    resp = {
        "order_id": order["id"],
        "out_trade_no": out_trade_no,
        "prepay_id": result.prepay_id,
        "qr_code_url": result.qr_code_url,
        "amount": plan["price_monthly"],
        "currency": "CNY",
        "tier": new_tier,
    }
    if jsapi_params:
        resp["jsapi_params"] = jsapi_params

    return jsonify(**resp), 201


@payment_bp.route("/payment/wechat/notify", methods=["POST"])
def wechat_pay_notify():
    """WeChat Pay 支付结果通知回调。

    该端点由微信服务器回调，不走用户认证。
    需验证签名后才能处理业务逻辑。
    """
    body = request.get_data(as_text=True)
    signature = request.headers.get(WECHAT_SIGNATURE_HEADER, "")
    serial = request.headers.get(WECHAT_SERIAL_HEADER, "")
    timestamp = request.headers.get(WECHAT_TIMESTAMP_HEADER, "")
    nonce = request.headers.get(WECHAT_NONCE_HEADER, "")

    api_v3_key = current_app.config.get("WECHAT_API_V3_KEY", "")

    # 签名验证
    if not verify_notify_sign(
        body=body,
        signature=signature,
        serial_no=serial,
        timestamp=timestamp,
        nonce=nonce,
        api_v3_key=api_v3_key,
    ):
        current_app.logger.warning("[wechat_pay] Notify signature verification FAILED")
        resp, code = build_notify_response(False)
        return resp, code, {"Content-Type": "application/json"}

    # 解析通知体
    result = parse_notify_body(body)
    if not result.success:
        current_app.logger.warning(f"[wechat_pay] Notify parse error: {result.error}")
        resp, code = build_notify_response(False)
        return resp, code, {"Content-Type": "application/json"}

    # 处理业务逻辑：标记订单已支付 + 升级用户 tier + 创建订阅
    db = current_app._db
    order = db.get_order_by_out_trade_no(result.out_trade_no)
    if not order:
        current_app.logger.error(f"[wechat_pay] Order not found: {result.out_trade_no}")
        resp, code = build_notify_response(True)  # 返回 SUCCESS 避免微信重复通知
        return resp, code, {"Content-Type": "application/json"}

    if order["status"] == "paid":
        # 幂等：已支付的订单直接返回成功
        resp, code = build_notify_response(True)
        return resp, code, {"Content-Type": "application/json"}

    # 原子操作：标记支付 → 升级 tier → 创建订阅
    paid_order = db.mark_order_paid(result.out_trade_no, result.transaction_id)
    if not paid_order:
        resp, code = build_notify_response(True)
        return resp, code, {"Content-Type": "application/json"}

    user_id = paid_order["user_id"]
    tier = paid_order["tier"]
    plan_id = paid_order["plan_id"]

    # 升级用户 tier
    db.update_user_tier(user_id, tier)

    # 创建/更新订阅（1 个月有效期）
    from datetime import datetime, timedelta
    expires = (datetime.now() + timedelta(days=30)).isoformat()
    db.upsert_subscription(user_id, tier, plan_id, expires, auto_renew=False)

    current_app.logger.info(
        f"[wechat_pay] Payment confirmed: user={user_id} tier={tier} "
        f"txn={result.transaction_id} order={result.out_trade_no}"
    )

    resp, code = build_notify_response(True)
    return resp, code, {"Content-Type": "application/json"}

