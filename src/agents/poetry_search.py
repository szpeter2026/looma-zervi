"""
Looma agents — 诗词向量检索（双后端：pgvector + Chroma）

优先使用 pgvector（与 looma-zervi 底座统一），
pgvector 不可用时自动回退到 Chroma（Tatha 现有数据）。

向量空间: pgvector 768d (nomic-embed-text) / Chroma 384d (all-MiniLM-L6-v2)

用法:
  from src.agents.poetry_search import search_poems
  results = search_poems("思乡的诗", n_results=5)
"""
from __future__ import annotations

import os
from functools import lru_cache

from src.core.config import get_settings

# pgvector 可用性缓存（避免每次查询都重试 Ollama 连接）
_pgvector_available: bool | None = None


def _check_pgvector() -> bool:
    """快速检测 pgvector 是否可用（缓存结果）"""
    global _pgvector_available
    if _pgvector_available is not None:
        return _pgvector_available

    settings = get_settings()
    try:
        import psycopg
        with psycopg.connect(settings.PG_DSN, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name='poetry';",
                    (settings.SCHEMA,),
                )
                _pgvector_available = cur.fetchone() is not None
    except Exception:
        _pgvector_available = False

    return _pgvector_available


def _search_pgvector(query: str, n_results: int = 5) -> list[dict] | None:
    """pgvector 后端检索（768d nomic-embed-text）"""
    if not _check_pgvector():
        return None

    settings = get_settings()
    dsn = settings.PG_DSN

    try:
        import psycopg
        from src.core.embeddings import get_embed_model

        embed_model = get_embed_model()
        query_embedding = embed_model.get_text_embedding(query)

        with psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
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

                return [
                    {
                        "title": row[0] or "",
                        "author": row[1] or "",
                        "dynasty": row[2] or "",
                        "content": row[3] or "",
                        "distance": float(row[4]) if row[4] is not None else None,
                    }
                    for row in rows
                ]

    except Exception as e:
        print(f"[poetry_search/pgvector] 检索失败: {e}", flush=True)
        return None


@lru_cache(maxsize=1)
def _get_chroma_collection():
    """懒加载 Chroma collection"""
    import chromadb

    chroma_path = os.getenv(
        "POETRY_CHROMA_PATH",
        "./data/poetry_full"
    )
    client = chromadb.PersistentClient(path=chroma_path)
    return client.get_collection("poetry_full")


def _search_chroma(query: str, n_results: int = 5) -> list[dict]:
    """Chroma 后端检索（384d all-MiniLM-L6-v2）"""
    try:
        collection = _get_chroma_collection()
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        poems = []
        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        dists_list = results.get("distances", [[]])[0]

        for i in range(len(ids_list)):
            meta = metas_list[i] if metas_list and i < len(metas_list) else {}
            poems.append({
                "title": meta.get("title", "") or "",
                "author": meta.get("author", "") or "",
                "dynasty": meta.get("dynasty", "") or "",
                "content": (docs_list[i] if docs_list and i < len(docs_list) else "") or "",
                "distance": float(dists_list[i]) if dists_list and i < len(dists_list) else None,
            })

        return poems

    except Exception as e:
        print(f"[poetry_search/chroma] 检索失败: {e}", flush=True)
        return []


_fallback_printed = False


def search_poems(query: str, n_results: int = 5) -> list[dict]:
    """
    向量检索诗词（双后端自动切换）。

    优先 pgvector，不可用时回退 Chroma。

    Args:
        query: 搜索关键词
        n_results: 返回结果数

    Returns:
        [{"title": ..., "author": ..., "dynasty": ..., "content": ..., "distance": ...}, ...]
    """
    global _fallback_printed

    # 尝试 pgvector
    result = _search_pgvector(query, n_results)
    if result is not None:
        return result

    # 回退 Chroma（只打印一次）
    if not _fallback_printed:
        print("[poetry_search] pgvector 不可用，使用 Chroma 后端", flush=True)
        _fallback_printed = True
    return _search_chroma(query, n_results)


def get_poetry_stats() -> dict:
    """获取诗词库统计（优先 pgvector，回退 Chroma）"""
    settings = get_settings()

    # 尝试 pgvector
    try:
        import psycopg
        with psycopg.connect(settings.PG_DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {settings.SCHEMA}.poetry;")
                count = cur.fetchone()[0]
                if count > 0:
                    return {"total": count, "backend": "pgvector", "schema": settings.SCHEMA}
    except Exception:
        pass

    # 回退 Chroma
    try:
        collection = _get_chroma_collection()
        return {
            "total": collection.count(),
            "backend": "Chroma (PersistentClient)",
            "path": os.getenv("POETRY_CHROMA_PATH", ""),
        }
    except Exception as e:
        return {"error": str(e)}


# ====== 命令行测试 ======
if __name__ == "__main__":
    print("=" * 50)
    print("诗词向量检索 - 双后端模式")
    print("=" * 50)

    stats = get_poetry_stats()
    print(f"\n当前后端: {stats}")

    queries = [
        "思乡",
        "大漠孤烟直",
        "春花秋月何时了",
    ]
    for q in queries:
        print(f"\n--- '{q}' ---")
        for i, r in enumerate(search_poems(q, 3)):
            print(f"  [{i+1}] 《{r['title']}》- {r['author']}({r['dynasty']}) dist={r['distance']:.4f}")
