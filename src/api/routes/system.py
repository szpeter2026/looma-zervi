"""Looma api — 路由：系统接口"""
from __future__ import annotations

import time

from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/v1/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "uptime_seconds": int(time.time())}
