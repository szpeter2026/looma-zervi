"""
Looma api — 配额控制

按 user_id + tier + 日 计数，支持 SQLite 持久化或进程内存回退。
来源：Tatha api/quota.py，已迁入 looma-zervi。
"""
from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Literal

from src.api.auth import Tier

# 资源名
RESOURCE_JOB_MATCH = "job_match"
RESOURCE_ASK = "ask"
RESOURCE_RESUME_PARSE = "resume_parse"
RESOURCE_RAG = "rag"

# 各档位每日上限（对齐 api.yaml v1.1.0: free / pro / enterprise）
QUOTA_LIMITS: dict[Tier, dict[str, int]] = {
    "free": {
        RESOURCE_JOB_MATCH: 3,
        RESOURCE_ASK: 10,
        RESOURCE_RESUME_PARSE: 1,
        RESOURCE_RAG: 5,
    },
    "pro": {
        RESOURCE_JOB_MATCH: 20,
        RESOURCE_ASK: 50,
        RESOURCE_RESUME_PARSE: 10,
        RESOURCE_RAG: 20,
    },
    "enterprise": {
        RESOURCE_JOB_MATCH: 99999,
        RESOURCE_ASK: 99999,
        RESOURCE_RESUME_PARSE: 99999,
        RESOURCE_RAG: 99999,
    },
}

# 各档位 top_n 上限
TOP_N_LIMIT: dict[Tier, int] = {
    "free": 3,
    "pro": 5,
    "enterprise": 20,
}

# 进程内内存回退
_memory: dict[str, int] = {}
_lock = Lock()


def _today_key() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _storage_key(user_id: str, resource: str) -> str:
    return f"quota:{user_id}:{resource}:{_today_key()}"


def get_remaining(user_id: str, tier: Tier, resource: str) -> int:
    """当前剩余配额。"""
    limit = QUOTA_LIMITS.get(tier, QUOTA_LIMITS["free"]).get(resource, 0)
    date = _today_key()

    # 优先 SQLite
    try:
        from src.db.manager import DBManager
        db = DBManager()
        record = db.get_quota(user_id, resource, date)
        if record:
            return max(0, limit - record["used"])
        return limit
    except Exception:
        pass

    # 回退内存
    key = _storage_key(user_id, resource)
    with _lock:
        used = _memory.get(key, 0)
    return max(0, limit - used)


def consume(user_id: str, tier: Tier, resource: str) -> bool:
    """扣减 1 次配额。返回 True=成功，False=超限。"""
    limit = QUOTA_LIMITS.get(tier, QUOTA_LIMITS["free"]).get(resource, 0)
    date = _today_key()

    # 优先 SQLite 原子扣减
    try:
        from src.db.manager import DBManager
        db = DBManager()
        return db.consume_quota(user_id, resource, date, limit)
    except Exception:
        pass

    # 回退内存
    key = _storage_key(user_id, resource)
    with _lock:
        used = _memory.get(key, 0)
        if used >= limit:
            return False
        _memory[key] = used + 1
    return True


def clamp_top_n(tier: Tier, requested: int) -> int:
    """按档位限制 top_n。"""
    max_n = TOP_N_LIMIT.get(tier, TOP_N_LIMIT["free"])
    return min(max(requested, 1), max_n)