"""Looma api — 路由：系统接口"""
from __future__ import annotations

import time

from fastapi import APIRouter

from src.api.app import PROCESS_START_TIME, llm_ready, embed_ready, pgvector_ready, rag_ready
from src.core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/v1/health")
async def health():
    from src.core.llm import get_active_provider, get_llm
    from src.core.llm_cache import get_llm_cache
    from src.core.embeddings import get_active_embed_provider
    from src.core.resilience import get_resilience_stats
    settings = get_settings()
    llm = get_llm()
    uptime = max(0, int(time.time() - PROCESS_START_TIME))
    return {
        "status": "ok",
        "version": "0.1.0",
        "uptime_seconds": uptime,
        "llm_provider": get_active_provider() or "unavailable",
        "llm_model": llm.model or settings.LLM_MODEL,
        "llm_provider_order": [p.strip() for p in settings.LLM_PROVIDER_ORDER.split(",") if p.strip()],
        "embed_provider": get_active_embed_provider() or "unavailable",
        "embed_provider_order": [p.strip() for p in settings.EMBED_PROVIDER_ORDER.split(",") if p.strip()],
        "llm_cache": get_llm_cache().stats(),
        "resilience": get_resilience_stats(),
        "dependencies": {
            "llm": llm.is_available,
            "embed": embed_ready,
            "pgvector": pgvector_ready,
            "rag_index": rag_ready,
        },
    }
