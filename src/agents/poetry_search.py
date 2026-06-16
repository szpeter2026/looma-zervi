"""
Looma agents — 诗词向量检索（pgvector 后端）

从 Tatha Chroma 诗词检索迁移至 pgvector，复用 looma-zervi 底座。
向量空间统一 768d（nomic-embed-text）。
"""
from __future__ import annotations

from src.core.config import get_settings
from src.retrieval.vector_store import get_vector_store


def search_poems(query: str, n_results: int = 5) -> list[dict]:
    """
    向量检索诗词。
    使用 pgvector 存储的诗词数据，按余弦距离排序。

    Args:
        query: 搜索关键词（如 "思乡"、"送别"）
        n_results: 返回结果数

    Returns:
        [{"title": ..., "author": ..., "dynasty": ..., "content": ..., "distance": ...}, ...]
    """
    settings = get_settings()
    dsn = settings.PG_DSN

    try:
        import psycopg
        from src.core.embeddings import get_embed_model

        # 获取 embedding
        embed_model = get_embed_model()
        query_embedding = embed_model.get_text_embedding(query)

        # 在 pgvector 中搜索
        with psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                # 检查 poetry 表是否存在
                cur.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name='poetry';",
                    (settings.SCHEMA,),
                )
                if not cur.fetchone():
                    return []

                # 向量余弦搜索
                embedding_str = f"[{', '.join(str(x) for x in query_embedding)}]"
                cur.execute(
                    f"""
                    SELECT title, author, dynasty, content, 
                           embedding <=> %s::vector AS distance
                    FROM {settings.SCHEMA}.poetry
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (embedding_str, embedding_str, n_results),
                )
                rows = cur.fetchall()

                poems = []
                for row in rows:
                    poems.append({
                        "title": row[0] or "",
                        "author": row[1] or "",
                        "dynasty": row[2] or "",
                        "content": row[3] or "",
                        "distance": float(row[4]) if row[4] is not None else None,
                    })
                return poems

    except Exception as e:
        # 若 pgvector 诗词表不存在或连接失败，返回空列表
        print(f"[poetry_search] 检索失败: {e}", flush=True)
        return []