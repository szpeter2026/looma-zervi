"""Looma api — 地区与定价路由"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])

# 默认定价
PRICING_CN: dict[str, Any] = {
    "currency": "CNY",
    "basic_monthly": 99,
    "basic_yearly": 599,
    "pro_monthly": 199,
    "pro_yearly": 1199,
}
PRICING_INTL: dict[str, Any] = {
    "currency": "USD",
    "basic_monthly": 9.9,
    "basic_yearly": 59,
    "pro_monthly": 19.9,
    "pro_yearly": 119,
}


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real = request.headers.get("X-Real-IP")
    if real:
        return real.strip()
    if request.client:
        return request.client.host or "127.0.0.1"
    return "127.0.0.1"


def _is_private_ip(ip: str) -> bool:
    if not ip or ip == "127.0.0.1" or ip.startswith("192.168.") or ip.startswith("10."):
        return True
    if ip == "::1" or ip.startswith("fe80:"):
        return True
    return False


def _get_country(request: Request) -> str:
    cf = request.headers.get("CF-IPCountry")
    if cf and len(cf) == 2:
        return cf.upper()
    default = os.environ.get("DEFAULT_REGION", "").strip().upper()
    if default and len(default) >= 2:
        return default[:2]
    return "CN"


@router.get("/v1/region")
def region(request: Request):
    """按请求来源返回地区与定价"""
    raw = (request.query_params.get("country") or request.query_params.get("region") or "").strip().upper()
    if raw == "INTL" or raw == "US" or raw == "EN":
        country = "US"
    elif raw == "CN" or raw == "CNY" or raw == "ZH":
        country = "CN"
    elif len(raw) >= 2:
        country = raw[:2]
    else:
        country = _get_country(request)

    pricing = PRICING_CN if country == "CN" else PRICING_INTL
    currency = pricing.get("currency", "CNY" if country == "CN" else "USD")
    locale = "zh-CN" if country == "CN" else "en-US"
    return {
        "country": country,
        "currency": currency,
        "locale": locale,
        "pricing": pricing,
    }