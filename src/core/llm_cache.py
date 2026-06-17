"""Looma core — LLM 请求级缓存（TTL + LRU）"""
from __future__ import annotations

import hashlib
import time
import threading
import logging
from collections import OrderedDict
from typing import Any

logger = logging.getLogger("looma.cache")


class LLMCache:
    """线程安全的 TTL + LRU 内存缓存，用于 LLM 调用结果缓存。"""

    def __init__(self, max_size: int = 256, ttl_seconds: int = 300):
        self._lock = threading.Lock()
        self._store: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _key(self, model: str, prompt: str) -> str:
        raw = f"{model}::{prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, model: str, prompt: str) -> str | None:
        key = self._key(model, prompt)
        with self._lock:
            if key in self._store:
                ts, val = self._store[key]
                if time.time() - ts < self._ttl:
                    self._store.move_to_end(key)
                    self._hits += 1
                    return val
                # 过期，删除
                del self._store[key]
        self._misses += 1
        return None

    def set(self, model: str, prompt: str, result: str) -> None:
        key = self._key(model, prompt)
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (time.time(), result)
            # LRU 淘汰
            while len(self._store) > self._max_size:
                self._store.popitem(last=False)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._store),
                "max_size": self._max_size,
                "ttl_seconds": self._ttl,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total, 4) if total else 0,
            }

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0


# 全局单例
_llm_cache: LLMCache | None = None


def get_llm_cache() -> LLMCache:
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LLMCache(max_size=256, ttl_seconds=300)
    return _llm_cache
