"""Looma retrieval — pgvector 统一向量存储"""
from __future__ import annotations

from llama_index.vector_stores.postgres import PGVectorStore
from src.core.config import get_settings


_vector_store: PGVectorStore | None = None


def get_vector_store() -> PGVectorStore:
    """获取全局 PGVectorStore 实例（懒加载，单例）"""
    global _vector_store
    if _vector_store is None:
        settings = get_settings()
        _vector_store = PGVectorStore.from_params(
            host=settings.PG_HOST,
            port=settings.PG_PORT,
            user=settings.PG_USER,
            password=settings.PG_PASSWORD,
            database=settings.PG_DATABASE,
            table_name=settings.TABLE,
            schema_name=settings.SCHEMA,
            embed_dim=settings.EMBED_DIM,
            hnsw_kwargs={
                "hnsw_m": 16,
                "hnsw_ef_construction": 64,
                "hnsw_ef_search": 40,
            },
        )
    return _vector_store


def reset_vector_store() -> None:
    """重置单例（测试用）"""
    global _vector_store
    _vector_store = None
