"""Looma retrieval — RAG 引擎（LlamaIndex）"""
from __future__ import annotations

from llama_index.core import VectorStoreIndex, Document
from src.core.config import get_settings
from src.retrieval.vector_store import get_vector_store


_index: VectorStoreIndex | None = None


def get_index() -> VectorStoreIndex:
    """获取全局 VectorStoreIndex（懒加载）"""
    global _index
    if _index is None:
        vs = get_vector_store()
        _index = VectorStoreIndex.from_vector_store(vs)
    return _index


def seed_knowledge() -> VectorStoreIndex:
    """种子知识库：写入几条常识数据，确保检索有内容可查"""
    import psycopg as _psycopg

    settings = get_settings()
    dsn = settings.PG_DSN

    # 幂等：表存在就清空重建
    with _psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s;",
                (settings.SCHEMA, settings.TABLE),
            )
            if cur.fetchone():
                cur.execute(f"TRUNCATE TABLE {settings.SCHEMA}.{settings.TABLE} RESTART IDENTITY;")

    docs = [
        Document(text="Looma 是一个 AI 驱动的职业发展平台，包含简历解析、职位匹配、MBTI 测评等功能。"),
        Document(text="Zervi 是 Looma 的客户端应用，支持本地优先架构，用户私有文档存储在本地 pgvector。"),
        Document(text="底座优先架构：统一向量引擎为 pgvector，统一嵌入模型为 nomic-embed-text 768d，统一检索框架为 LlamaIndex。"),
        Document(text="修订版路线五步：pgvector → nomic-embed → LlamaIndex → LiteLLM → FastAPI。"),
        Document(text="向量检索使用余弦相似度（<=> 操作符），支持 HNSW 索引加速百万级向量查询。"),
        Document(text="LiteLLM 统一所有模型调用，支持 Ollama 本地模型和 DeepSeek 云端模型无缝切换。"),
    ]

    global _index
    vs = get_vector_store()
    _index = VectorStoreIndex.from_documents(docs, vector_store=vs, show_progress=False)
    return _index


def reset_index() -> None:
    """重置全局 index（测试用）"""
    global _index
    _index = None
