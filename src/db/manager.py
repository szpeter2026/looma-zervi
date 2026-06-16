"""
Looma db — 数据库管理器

管理 SQLite 元数据库：文档、分块、查询日志。
来源：DemoPeter db_manager.py，已迁入 looma-zervi。
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

from src.core.config import get_settings

# 元数据库表结构
SCHEMA_SQL = """
-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    doc_type TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    processed_at TEXT
);

-- 分块表
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    char_count INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 查询日志表
CREATE TABLE IF NOT EXISTS query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    provider TEXT NOT NULL,
    response_time_ms REAL DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    tier TEXT DEFAULT 'free',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 配额记录表
CREATE TABLE IF NOT EXISTS quota_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    resource TEXT NOT NULL,
    date TEXT NOT NULL,
    used INTEGER DEFAULT 0,
    daily_limit INTEGER NOT NULL,
    UNIQUE(user_id, resource, date)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_time ON query_logs(created_at);
"""


class DBManager:
    """元数据库管理器 — SQLite 为核心"""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            settings = get_settings()
            db_dir = Path(__file__).resolve().parent.parent.parent / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(db_dir / "looma.db")
        else:
            self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        """初始化数据库表结构"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    # ===== 文档管理 =====

    def register_document(self, title: str, file_path: str, doc_type: str,
                          file_size: int = 0, metadata: dict | None = None) -> int:
        """注册新文档"""
        with self._conn() as conn:
            cursor = conn.execute(
                """INSERT INTO documents (title, file_path, doc_type, file_size, metadata, status, created_at)
                   VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
                (title, file_path, doc_type, file_size, json.dumps(metadata or {}),
                 datetime.now().isoformat())
            )
            conn.commit()
            return cursor.lastrowid

    def update_document_status(self, doc_id: int, status: str, chunk_count: int = 0):
        """更新文档处理状态"""
        with self._conn() as conn:
            conn.execute(
                "UPDATE documents SET status=?, chunk_count=?, processed_at=? WHERE id=?",
                (status, chunk_count, datetime.now().isoformat(), doc_id)
            )
            conn.commit()

    def get_documents(self, status: str | None = None) -> list[dict]:
        """查询文档列表"""
        with self._conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE status=? ORDER BY created_at DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM documents ORDER BY created_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def get_document(self, doc_id: int) -> dict | None:
        """获取单个文档"""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
            return dict(row) if row else None

    def delete_document(self, doc_id: int):
        """删除文档及关联数据"""
        with self._conn() as conn:
            conn.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))
            conn.commit()

    # ===== 分块管理 =====

    def save_chunks(self, doc_id: int, chunks: list[dict]):
        """批量保存文档分块"""
        with self._conn() as conn:
            conn.executemany(
                """INSERT INTO chunks (document_id, chunk_index, content, char_count, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                [(doc_id, c["index"], c["content"], len(c["content"]),
                  json.dumps(c.get("metadata", {})))
                 for c in chunks]
            )
            conn.commit()

    def get_chunks(self, doc_id: int) -> list[dict]:
        """获取文档的所有分块"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM chunks WHERE document_id=? ORDER BY chunk_index", (doc_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ===== 查询日志 =====

    def log_query(self, query_text: str, provider: str, response_time_ms: float,
                  chunk_count: int = 0):
        """记录查询日志"""
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO query_logs (query_text, provider, response_time_ms, chunk_count, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (query_text, provider, response_time_ms, chunk_count, datetime.now().isoformat())
            )
            conn.commit()

    # ===== 统计 =====

    def get_stats(self) -> dict:
        """获取知识库统计"""
        with self._conn() as conn:
            doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            doc_done = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE status='completed'").fetchone()[0]
            chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            total_chars = conn.execute(
                "SELECT COALESCE(SUM(char_count), 0) FROM chunks").fetchone()[0]
            query_count = conn.execute("SELECT COUNT(*) FROM query_logs").fetchone()[0]
            return {
                "documents_total": doc_count,
                "documents_completed": doc_done,
                "documents_pending": doc_count - doc_done,
                "chunks_total": chunk_count,
                "total_characters": total_chars,
                "queries_total": query_count,
            }

    def get_recent_queries(self, limit: int = 20) -> list[dict]:
        """获取最近查询"""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM query_logs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ===== 用户与配额 =====

    def get_user(self, user_id: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
            return dict(row) if row else None

    def get_user_by_email(self, email: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            return dict(row) if row else None

    def create_user(self, user_id: str, email: str, password_hash: str, tier: str = "free"):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO users (id, email, password_hash, tier) VALUES (?, ?, ?, ?)",
                (user_id, email, password_hash, tier),
            )
            conn.commit()

    def get_quota(self, user_id: str, resource: str, date: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM quota_records WHERE user_id=? AND resource=? AND date=?",
                (user_id, resource, date),
            ).fetchone()
            return dict(row) if row else None

    def consume_quota(self, user_id: str, resource: str, date: str, limit: int) -> bool:
        """原子扣减配额，返回 True=成功，False=超限"""
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT used FROM quota_records WHERE user_id=? AND resource=? AND date=?",
                (user_id, resource, date),
            ).fetchone()
            if existing:
                used = existing[0]
                if used >= limit:
                    return False
                conn.execute(
                    "UPDATE quota_records SET used=used+1 WHERE user_id=? AND resource=? AND date=?",
                    (user_id, resource, date),
                )
            else:
                conn.execute(
                    "INSERT INTO quota_records (user_id, resource, date, used, daily_limit) VALUES (?, ?, ?, 1, ?)",
                    (user_id, resource, date, limit),
                )
            conn.commit()
            return True