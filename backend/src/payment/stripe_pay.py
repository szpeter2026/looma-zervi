"""
Stripe payment integration for overseas market.

Provides the same interface contract as wechat_pay.py:
  - create_checkout_session()  → equivalent to create_native_order / create_jsapi_order
  - verify_webhook()           → equivalent to verify_notify_sign
  - parse_webhook_event()      → equivalent to parse_notify_body

Payment flow (Stripe Checkout):
  1. Client calls POST /v1/payment/stripe/checkout with {tier, period}
  2. Backend creates Stripe Checkout Session → returns session URL
  3. User is redirected to Stripe-hosted payment page (card / Apple Pay / Google Pay)
  4. After payment, Stripe redirects to success_url + sends webhook
  5. Webhook handler verifies signature, marks order paid, upgrades tier

For subscriptions (recurring):
  - Use Stripe Customer + Subscription instead of one-time Checkout
  - Webhook handles invoice.paid / customer.subscription.deleted events

Required env vars:
  - STRIPE_SECRET_KEY      sk_live_xxx or sk_test_xxx
  - STRIPE_WEBHOOK_SECRET  whsec_xxx (from Stripe Dashboard → Webhooks)

Reference: https://stripe.com/docs/api
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import requests

STRIPE_API_BASE = "https://api.stripe.com/v1"
STRIPE_CHECKOUT_SESSIONS = "/checkout/sessions"
STRIPE_CUSTOMERS = "/customers"
STRIPE_SUBSCRIPTIONS = "/subscriptions"


@dataclass
class StripeCheckoutResult:
    """Stripe Checkout Session creation result."""
    session_id: str
    session_url: str           # URL to redirect user to Stripe-hosted checkout
    out_trade_no: str           # internal order number (metadata)
    payment_intent_id: str = ""


@dataclass
class StripeWebhookResult:
    """Stripe webhook event processing result."""
    success: bool
    event_type: str = ""        # checkout.session.completed / invoice.paid / etc.
    out_trade_no: str = ""
    customer_id: str = ""
    subscription_id: str = ""
    amount_total: int = 0       # in cents
    currency: str = "USD"
    error: str = ""


# ============================================================
# Stripe API helper
# ============================================================

def _stripe_request(method: str, path: str, secret_key: str,
                    data: dict = None, params: dict = None) -> dict:
    """Make an authenticated request to Stripe API."""
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    url = f"{STRIPE_API_BASE}{path}"

    if method == "POST":
        resp = requests.post(url, data=data or {}, headers=headers, timeout=15)
    else:
        resp = requests.get(url, params=params or {}, headers=headers, timeout=15)

    if resp.status_code >= 400:
        raise ValueError(f"Stripe API error {resp.status_code}: {resp.text}")

    return resp.json()


# ============================================================
# Create Checkout Session
# ============================================================

def create_checkout_session(
    secret_key: str,
    out_trade_no: str,
    tier: str,
    amount_cents: int,         # e.g. 199 = $1.99
    currency: str = "USD",
    plan_name: str = "Looma Supporter",
    success_url: str = "",
    cancel_url: str = "",
    customer_email: str = "",
    mode: str = "payment",     # payment | subscription
    price_id: str = "",        # Stripe Price ID for subscription mode
) -> StripeCheckoutResult:
    """Create a Stripe Checkout Session.

    For one-time payment: mode=payment, amount_cents required.
    For subscription: mode=subscription, price_id required (replaces amount).

    Returns session_id + session_url for client redirect.
    """
    data = {
        "mode": mode,
        "client_reference_id": out_trade_no,
        "metadata[out_trade_no]": out_trade_no,
        "metadata[tier]": tier,
    }

    if success_url:
        data["success_url"] = success_url
    if cancel_url:
        data["cancel_url"] = cancel_url
    if customer_email:
        data["customer_email"] = customer_email

    if mode == "payment":
        data["line_items[0][quantity]"] = "1"
        data["line_items[0][price_data][currency]"] = currency.lower()
        data["line_items[0][price_data][unit_amount]"] = str(amount_cents)
        data["line_items[0][price_data][product_data][name]"] = plan_name
    elif mode == "subscription" and price_id:
        data["line_items[0][quantity]"] = "1"
        data["line_items[0][price]"] = price_id

    result = _stripe_request("POST", STRIPE_CHECKOUT_SESSIONS, secret_key, data)

    return StripeCheckoutResult(
        session_id=result.get("id", ""),
        session_url=result.get("url", ""),
        out_trade_no=out_trade_no,
        payment_intent_id=result.get("payment_intent", ""),
    )


# ============================================================
# Webhook verification
# ============================================================

def verify_webhook_signature(
    payload: bytes,
    sig_header: str,
    webhook_secret: str,
    tolerance: int = 300,
) -> bool:
    """Verify Stripe webhook signature.

    Stripe uses HMAC-SHA256 with a timestamp to prevent replay attacks.
    Format: t=timestamp,v1=signature

    Raises ValueError if verification fails.
    """
    if not webhook_secret:
        return True  # dev mode: skip verification

    import hmac
    import hashlib

    try:
        elements = dict(e.split("=", 1) for e in sig_header.split(","))
        timestamp = int(elements.get("t", "0"))
        v1_signature = elements.get("v1", "")
    except (ValueError, KeyError):
        raise ValueError("Invalid Stripe webhook header format")

    # Check timestamp tolerance (replay attack prevention)
    current_time = int(time.time())
    if abs(current_time - timestamp) > tolerance:
        raise ValueError("Stripe webhook timestamp outside tolerance")

    # Compute expected signature
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    expected_sig = hmac.new(
        webhook_secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, v1_signature):
        raise ValueError("Stripe webhook signature verification failed")

    return True


def parse_webhook_event(payload: bytes) -> StripeWebhookResult:
    """Parse a Stripe webhook event and extract payment info.

    Handles:
    - checkout.session.completed (one-time payment)
    - invoice.paid (subscription recurring payment)
    - customer.subscription.deleted (subscription cancelled)
    """
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return StripeWebhookResult(success=False, error="Invalid JSON")

    event_type = event.get("type", "")
    obj = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        out_trade_no = obj.get("client_reference_id", "")
        amount_total = obj.get("amount_total", 0)
        currency = obj.get("currency", "USD")
        customer_id = obj.get("customer", "")

        return StripeWebhookResult(
            success=True,
            event_type=event_type,
            out_trade_no=out_trade_no,
            customer_id=customer_id,
            amount_total=amount_total,
            currency=currency.upper(),
        )

    elif event_type == "invoice.paid":
        metadata = obj.get("metadata", {})
        out_trade_no = metadata.get("out_trade_no", "")
        amount_total = obj.get("amount_paid", 0)
        currency = obj.get("currency", "USD")
        customer_id = obj.get("customer", "")
        subscription_id = obj.get("subscription", "")

        return StripeWebhookResult(
            success=True,
            event_type=event_type,
            out_trade_no=out_trade_no,
            customer_id=customer_id,
            subscription_id=subscription_id,
            amount_total=amount_total,
            currency=currency.upper(),
        )

    elif event_type == "customer.subscription.deleted":
        customer_id = obj.get("customer", "")
        subscription_id = obj.get("id", "")

        return StripeWebhookResult(
            success=True,
            event_type=event_type,
            customer_id=customer_id,
            subscription_id=subscription_id,
        )

    else:
        return StripeWebhookResult(
            success=True,
            event_type=event_type,
        )


# ============================================================
# Generate order number
# ============================================================

def generate_out_trade_no() -> str:
    """Generate unique internal order number for Stripe payments.

    Format: LOOMA + YYYYMMDDHHmmss + 8hex (same format as WeChat Pay)
    """
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = uuid.uuid4().hex[:8].upper()
    return f"LOOMA{ts}{rand}"
