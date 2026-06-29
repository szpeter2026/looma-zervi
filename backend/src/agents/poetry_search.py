"""
Poetry search — search poems via ChromaDB or pgvector.

Migrated from old poetry_search.py, adapted for Flask + ChromaDB primary.
"""
from __future__ import annotations
import logging
import requests
from flask import current_app

logger = logging.getLogger("looma.poetry")


def search_poems(query: str, n_results: int = 3) -> list[dict]:
    """Search poems by query text via ChromaDB.

    Returns list of dicts with title, author, dynasty, content, theme.
    Falls back to pgvector if ChromaDB unavailable.
    """
    try:
        from src.rag.chroma_client import search_chroma
        results = search_chroma(query, n_results=n_results, collection="looma_poetry")
        poems = []
        for r in results:
            meta = r.get("metadata", {})
            poems.append({
                "title": meta.get("title", ""),
                "author": meta.get("author", ""),
                "dynasty": meta.get("dynasty", ""),
                "content": r.get("content", ""),
                "theme": meta.get("theme", ""),
            })
        return poems
    except Exception as e:
        logger.warning(f"ChromaDB poetry search failed: {e}")

    # Fallback: pgvector
    try:
        config = current_app.config
        dsn = config.get("PG_DSN", "")
        if not dsn:
            return []

        import psycopg
        with psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Use simple text matching for fallback
                cur.execute(
                    """SELECT title, author, dynasty, content, theme
                       FROM looma.poetry
                       WHERE title ILIKE %s OR content ILIKE %s OR theme ILIKE %s
                       LIMIT %s""",
                    (f"%{query}%", f"%{query}%", f"%{query}%", n_results)
                )
                rows = cur.fetchall()
                return [
                    {"title": r[0], "author": r[1], "dynasty": r[2], "content": r[3], "theme": r[4]}
                    for r in rows
                ]
    except Exception as e2:
        logger.warning(f"pgvector poetry fallback failed: {e2}")
        return []
