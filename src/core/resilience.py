"""Looma core — 调用弹性策略：超时、重试、熔断

为 LLM 和 Embedding 调用提供统一的容错机制：
- 调用超时（per-call timeout）
- 自动重试（指数退避，最多 2 次）
- 熔断器（连续失败 N 次后短路一段时间，防止雪崩）
"""

from __future__ import annotations

import logging
import threading
import time
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger("looma.resilience")

F = TypeVar("F", bound=Callable)


class CircuitBreaker:
    """简单熔断器：连续失败 threshold 次后进入 OPEN 状态，cooldown 秒后变为 HALF_OPEN。

    状态机: CLOSED → (failures >= threshold) → OPEN → (cooldown elapsed) → HALF_OPEN
            HALF_OPEN → (success) → CLOSED  |  (failure) → OPEN
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, name: str, failure_threshold: int = 5, cooldown_seconds: float = 30.0):
        self.name = name
        self._failure_threshold = failure_threshold
        self._cooldown = cooldown_seconds
        self._lock = threading.Lock()
        self._state = self.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._last_state_change: float = time.time()

    @property
    def state(self) -> str:
        with self._lock:
            self._transition()
            return self._state

    def _transition(self):
        now = time.time()
        if self._state == self.OPEN and (now - self._last_state_change) >= self._cooldown:
            self._state = self.HALF_OPEN
            self._last_state_change = now
            logger.info(f"熔断器 [{self.name}] OPEN -> HALF_OPEN (cooldown elapsed)")

    def allow_request(self) -> bool:
        with self._lock:
            self._transition()
            if self._state == self.OPEN:
                return False
            return True

    def record_success(self):
        with self._lock:
            if self._state == self.HALF_OPEN:
                self._state = self.CLOSED
                self._last_state_change = time.time()
                logger.info(f"熔断器 [{self.name}] HALF_OPEN -> CLOSED (success)")
            self._failure_count = 0

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._state == self.HALF_OPEN or (
                self._state == self.CLOSED and self._failure_count >= self._failure_threshold
            ):
                self._state = self.OPEN
                self._last_state_change = time.time()
                logger.warning(
                    f"熔断器 [{self.name}] -> OPEN ({self._failure_count} consecutive failures)"
                )

    def stats(self) -> dict:
        with self._lock:
            return {
                "name": self.name,
                "state": self._state,
                "failure_count": self._failure_count,
                "threshold": self._failure_threshold,
                "cooldown_s": self._cooldown,
            }


# ── 全局熔断器实例 ──

_llm_cb: CircuitBreaker | None = None
_embed_cb: CircuitBreaker | None = None


def get_llm_circuit_breaker() -> CircuitBreaker:
    global _llm_cb
    if _llm_cb is None:
        _llm_cb = CircuitBreaker(name="llm", failure_threshold=5, cooldown_seconds=30.0)
    return _llm_cb


def get_embed_circuit_breaker() -> CircuitBreaker:
    global _embed_cb
    if _embed_cb is None:
        _embed_cb = CircuitBreaker(name="embed", failure_threshold=5, cooldown_seconds=30.0)
    return _embed_cb


# ── 重试装饰器 ──

def with_retry(
    max_retries: int = 2,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    circuit_breaker: CircuitBreaker | None = None,
    timeout: float | None = None,
    operation_name: str = "call",
):
    """为函数添加重试 + 熔断 + 超时保护。

    Args:
        max_retries: 最大重试次数（不含首次调用）
        base_delay: 首次重试延迟（秒）
        backoff_factor: 指数退避因子
        circuit_breaker: 可选熔断器
        timeout: 可选超时（秒）
        operation_name: 操作名称（用于日志）
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 熔断检查
            if circuit_breaker is not None and not circuit_breaker.allow_request():
                raise RuntimeError(
                    f"熔断器 [{circuit_breaker.name}] 已断开，拒绝 {operation_name}"
                )

            last_exception = None
            delay = base_delay

            for attempt in range(max_retries + 1):
                try:
                    if timeout is not None:
                        import concurrent.futures

                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(func, *args, **kwargs)
                            result = future.result(timeout=timeout)
                    else:
                        result = func(*args, **kwargs)

                    # 成功：记录到熔断器
                    if circuit_breaker is not None:
                        circuit_breaker.record_success()
                    return result

                except Exception as e:
                    last_exception = e
                    if circuit_breaker is not None:
                        circuit_breaker.record_failure()

                    if attempt < max_retries:
                        logger.warning(
                            f"{operation_name} 第 {attempt + 1}/{max_retries + 1} 次失败: {e}，"
                            f"{delay:.1f}s 后重试"
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"{operation_name} 全部 {max_retries + 1} 次尝试失败: {e}"
                        )

            raise last_exception  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator


# ── 全局超时/重试配置（可通过环境变量覆盖）──

import os

LLM_CALL_TIMEOUT: float = float(os.getenv("LLM_CALL_TIMEOUT", "120.0"))
LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
EMBED_CALL_TIMEOUT: float = float(os.getenv("EMBED_CALL_TIMEOUT", "30.0"))
EMBED_MAX_RETRIES: int = int(os.getenv("EMBED_MAX_RETRIES", "2"))


def get_resilience_stats() -> dict:
    """获取所有弹性策略的统计信息（供健康检查）。"""
    return {
        "llm_circuit_breaker": get_llm_circuit_breaker().stats(),
        "embed_circuit_breaker": get_embed_circuit_breaker().stats(),
        "llm_timeout": LLM_CALL_TIMEOUT,
        "llm_max_retries": LLM_MAX_RETRIES,
        "embed_timeout": EMBED_CALL_TIMEOUT,
        "embed_max_retries": EMBED_MAX_RETRIES,
    }
