"""Looma api — 路由：系统接口"""
from __future__ import annotations

import time

from fastapi import APIRouter

from src.api.app import PROCESS_START_TIME, ollama_ready, pgvector_ready, rag_ready

router = APIRouter(tags=["system"])


@router.get("/v1/health")
async def health():
    from src.core.llm import get_active_provider
    from src.core.llm_cache import get_llm_cache
    from src.core.embeddings import get_active_embed_provider
    from src.core.resilience import get_resilience_stats
    uptime = max(0, int(time.time() - PROCESS_START_TIME))
    cache_stats = get_llm_cache().stats()
    return {
        "status": "ok",
        "version": "0.1.0",
        "uptime_seconds": uptime,
        "llm_provider": get_active_provider() or "unavailable",
        "embed_provider": get_active_embed_provider() or "unavailable",
        "llm_cache": cache_stats,
        "resilience": get_resilience_stats(),
        "dependencies": {
            "ollama": ollama_ready,
            "pgvector": pgvector_ready,
            "rag_index": rag_ready,
        },
    }
