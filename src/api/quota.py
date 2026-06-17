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

# 各档位每日上限（guest: 游客体验 / free: 注册免费 / pro / enterprise）
QUOTA_LIMITS: dict[Tier, dict[str, int]] = {
    "guest": {
        RESOURCE_JOB_MATCH: 1,
        RESOURCE_ASK: 3,
        RESOURCE_RESUME_PARSE: 1,
        RESOURCE_RAG: 2,
    },
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

# 游客配额耗尽后的升级引导信息
UPGRADE_HINT_GUEST_EXHAUSTED = {
    "reason": "guest_quota_exhausted",
    "message": "🎉 今日免费体验次数已用完（3次）。注册账号即可解锁每日10次AI问答，还有职位匹配、诗词推荐等更多功能！",
    "register_url": "/v1/auth/register",
    "upgrade_tiers": [
        {
            "tier": "free",
            "name": "免费版",
            "daily_quota": 10,
            "price_monthly": "免费",
            "features": ["每日10次AI问答", "3次职位匹配", "1次简历解析", "基础诗词推荐"],
        },
        {
            "tier": "pro",
            "name": "专业版",
            "daily_quota": 50,
            "price_monthly": "¥199/月",
            "features": ["每日50次AI问答", "20次职位匹配", "10次简历解析", "MBTI性格分析", "高级诗词RAG"],
        },
    ],
}

UPGRADE_HINT_FREE_EXHAUSTED = {
    "reason": "free_quota_exhausted",
    "message": "📈 今日免费版配额已用尽。升级专业版解锁每日50次AI问答、MBTI性格分析、高级诗词RAG等更多功能！",
    "register_url": None,
    "upgrade_tiers": [
        {
            "tier": "pro",
            "name": "专业版",
            "daily_quota": 50,
            "price_monthly": "¥199/月",
            "features": ["每日50次AI问答", "20次职位匹配", "10次简历解析", "MBTI性格分析", "高级诗词RAG"],
        },
        {
            "tier": "enterprise",
            "name": "企业版",
            "daily_quota": 99999,
            "price_monthly": "联系销售",
            "features": ["无限AI问答", "私有云部署", "数据隔离", "专属支持"],
        },
    ],
}

UPGRADE_HINT_SCOPE_FORBIDDEN = {
    "reason": "scope_forbidden",
    "message": "🔒 当前免费版仅支持公开知识库查询。升级专业版可解锁私有文档上传和检索。",
    "register_url": None,
    "upgrade_tiers": [
        {
            "tier": "pro",
            "name": "专业版",
            "daily_quota": 50,
            "price_monthly": "¥199/月",
            "features": ["私有文档上传", "文档管理", "高级检索"],
        },
    ],
}


def build_upgrade_hint(tier: Tier, used: int, reason: str = "quota_exhausted") -> dict:
    """根据档位和原因构建升级引导信息"""
    if reason == "scope_forbidden":
        hint = dict(UPGRADE_HINT_SCOPE_FORBIDDEN)
        hint["daily_limit"] = QUOTA_LIMITS.get(tier, QUOTA_LIMITS["guest"]).get(RESOURCE_ASK, 0)
        hint["used"] = used
        return hint

    if tier == "guest":
        hint = dict(UPGRADE_HINT_GUEST_EXHAUSTED)
    else:
        hint = dict(UPGRADE_HINT_FREE_EXHAUSTED)

    hint["daily_limit"] = QUOTA_LIMITS.get(tier, QUOTA_LIMITS["guest"]).get(RESOURCE_ASK, 0)
    hint["used"] = used
    return hint

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
    limit = QUOTA_LIMITS.get(tier, QUOTA_LIMITS["guest"]).get(resource, 0)
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
    limit = QUOTA_LIMITS.get(tier, QUOTA_LIMITS["guest"]).get(resource, 0)
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
    max_n = TOP_N_LIMIT.get(tier, TOP_N_LIMIT["guest"])
    return min(max(requested, 1), max_n)