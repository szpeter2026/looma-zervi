"""Looma core — Embedding 统一（nomic-embed-text 768d）"""
from __future__ import annotations

from llama_index.embeddings.ollama import OllamaEmbedding
from src.core.config import get_settings


def get_embed_model() -> OllamaEmbedding:
    """获取全局 Embedding 模型实例"""
    settings = get_settings()
    return OllamaEmbedding(
        model_name=settings.EMBED_MODEL,
        base_url=settings.OLLAMA_HOST,
        ollama_additional_kwargs={"dim": settings.EMBED_DIM},
    )
