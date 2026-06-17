"""Looma core — LLM 统一调用（LiteLLM + 多 Provider fallback + 缓存 + 重试/熔断）"""
from __future__ import annotations

import logging
import os
import time
import urllib.request
from typing import Optional

from llama_index.llms.litellm import LiteLLM
from src.core.config import get_settings
from src.core.llm_cache import get_llm_cache
from src.core.resilience import (
    get_llm_circuit_breaker,
    LLM_CALL_TIMEOUT,
    LLM_MAX_RETRIES,
)

logger = logging.getLogger("looma.llm")

# 当前活跃的 provider（供健康检查展示）
_active_provider: str = ""
_llm_instance: "CachedLiteLLM" | None = None


class _FallbackLiteLLM:
    """多 Provider fallback 包装：按 `LLM_PROVIDER_ORDER` 中的 provider 名称顺序尝试初始化。

    支持的 provider: 'ollama', 'openai', 'deepseek'.
    对每个 provider，优先使用对应的 *_MODEL env（如 OLLAMA_MODEL），否则回退到 LLM_MODEL。
    对于远程 provider 先做简单可用性检查（例如检查 API key 或 Ollama host）。
    """

    def __init__(self, temperature: float = 0.3):
        global _active_provider
        settings = get_settings()
        self._temperature = temperature
        # provider 列表
        self._providers = [p.strip().lower() for p in settings.LLM_PROVIDER_ORDER.split(",") if p.strip()]

        self._current_idx = 0
        self._current_provider: str = ""
        self._current_model: str = ""
        self._llm: Optional[LiteLLM] = None
        # LlamaIndex 需要 metadata 属性来识别 LLM
        self.metadata = type("_MD", (), {"model_name": settings.LLM_MODEL, "is_chat_model": False})()

        # 尝试找到第一个可用的 provider
        self._try_next_provider()
        _active_provider = self._current_provider or "unavailable"

    def _check_ollama(self, settings) -> bool:
        try:
            url = settings.OLLAMA_HOST.rstrip("/") + "/v1/models"
            with urllib.request.urlopen(url, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _configure_provider_env(self, provider: str, settings) -> None:
        if provider == "ollama":
            os.environ["OLLAMA_HOST"] = settings.OLLAMA_HOST
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
            if settings.OPENAI_BASE_URL:
                os.environ["OPENAI_BASE_URL"] = settings.OPENAI_BASE_URL
        elif provider == "deepseek":
            os.environ["OPENAI_API_KEY"] = settings.DEEPSEEK_API_KEY
            base_url = settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com/v1"
            os.environ["OPENAI_BASE_URL"] = base_url

    def _normalize_model_name(self, provider: str, model_name: str) -> str:
        if provider in ("openai", "deepseek") and "/" not in model_name:
            return f"{provider}/{model_name}"
        if provider == "ollama" and "/" not in model_name:
            return f"ollama/{model_name}"
        return model_name

    def _try_next_provider(self) -> bool:
        global _active_provider
        settings = get_settings()
        while self._current_idx < len(self._providers):
            prov = self._providers[self._current_idx]
            self._current_idx += 1
            model_name = settings.LLM_MODEL
            if prov == "ollama":
                if settings.OLLAMA_MODEL:
                    model_name = settings.OLLAMA_MODEL
                # 快速可用性检查
                if not self._check_ollama(settings):
                    logger.warning("Ollama 不可达，跳过 Ollama provider")
                    continue
            elif prov == "openai":
                if settings.OPENAI_MODEL:
                    model_name = settings.OPENAI_MODEL
                if not settings.OPENAI_API_KEY:
                    logger.warning("未配置 OPENAI_API_KEY，跳过 OpenAI provider")
                    continue
            elif prov == "deepseek":
                if settings.DEEPSEEK_MODEL:
                    model_name = settings.DEEPSEEK_MODEL
                if not settings.DEEPSEEK_API_KEY:
                    logger.warning("未配置 DEEPSEEK_API_KEY，跳过 DeepSeek provider")
                    continue
            else:
                # 未知 provider，尝试将其当作 model 标识使用
                model_name = prov

            model_name = self._normalize_model_name(prov, model_name)
            self._configure_provider_env(prov, settings)

            # 尝试初始化 LLM
            try:
                self._llm = LiteLLM(model=model_name, temperature=self._temperature)
                self._current_provider = prov
                self._current_model = model_name
                self.metadata.model_name = model_name
                logger.info(f"LLM provider 已连接: {prov} -> {model_name}")
                # 更新全局活跃 provider
                _active_provider = self._current_provider
                return True
            except Exception as e:
                logger.warning(f"Provider {prov} 初始化失败 ({model_name}): {e}")
                self._llm = None
                self._current_model = ""
                self._current_provider = ""
                continue

        logger.error("所有 LLM provider 均不可用")
        _active_provider = "unavailable"
        return False

    def complete(self, prompt: str, **kwargs):
        """带重试、熔断、超时的 LLM complete 调用。"""
        cb = get_llm_circuit_breaker()

        # 熔断检查
        if not cb.allow_request():
            raise RuntimeError(f"LLM 熔断器已断开（{cb.stats()['failure_count']} 次连续失败），拒绝请求")

        # 检查当前 provider 是否可用
        if self._llm is None:
            if not self._try_next_provider():
                raise RuntimeError("无可用的 LLM provider")

        # 重试循环（含 provider fallback）
        last_exception = None
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                # 带超时调用
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._llm.complete, prompt, **kwargs)
                    result = future.result(timeout=LLM_CALL_TIMEOUT)

                # 成功
                cb.record_success()
                return result

            except concurrent.futures.TimeoutError:
                last_exception = TimeoutError(f"LLM {self._current_provider} 调用超时 ({LLM_CALL_TIMEOUT}s)")
                cb.record_failure()
                logger.warning(
                    f"LLM {self._current_provider} 超时 (attempt {attempt + 1}/{LLM_MAX_RETRIES + 1})"
                )
            except Exception as e:
                last_exception = e
                cb.record_failure()
                logger.warning(
                    f"LLM {self._current_provider} 调用失败 (attempt {attempt + 1}/{LLM_MAX_RETRIES + 1}): {e}"
                )

            # 退避等待后重试
            if attempt < LLM_MAX_RETRIES:
                delay = 0.5 * (2 ** attempt)
                logger.info(f"LLM 重试等待 {delay:.1f}s...")
                time.sleep(delay)

            # 最后一次尝试失败后，尝试切换 provider
            if attempt == LLM_MAX_RETRIES:
                logger.warning(f"LLM {self._current_provider} 全部重试失败，尝试下一个 provider")
                if self._try_next_provider():
                    logger.info(f"已切换到 provider: {self._current_provider}")
                    # 新 provider 再尝试一次
                    try:
                        result = self._llm.complete(prompt, **kwargs)
                        cb.record_success()
                        return result
                    except Exception as e2:
                        last_exception = e2
                        cb.record_failure()
                        logger.error(f"新 provider {self._current_provider} 也调用失败: {e2}")

        raise last_exception or RuntimeError("LLM 调用失败")

    def __getattr__(self, name):
        if self._llm is None:
            raise RuntimeError("无可用的 LLM provider")
        return getattr(self._llm, name)

    @property
    def model(self) -> str:
        return self._current_model

    @property
    def provider(self) -> str:
        return self._current_provider

    @property
    def is_available(self) -> bool:
        return self._llm is not None


class CachedLiteLLM:
    """带缓存的 LiteLLM 代理，对相同 prompt 命中后 <1ms 返回。"""

    def __init__(self, model: str, temperature: float = 0.3):
        self._fallback = _FallbackLiteLLM(temperature=temperature)
        self._model = model  # 主 model 名（用于缓存 key 前缀）
        self._cache = get_llm_cache()
        # 代理 metadata 到内部 fallback
        self.metadata = self._fallback.metadata

    def complete(self, prompt: str, **kwargs):
        """同步 complete，命中缓存直接返回。"""
        actual_model = self._fallback.model or self._model
        cached = self._cache.get(actual_model, prompt)
        if cached is not None:
            logger.debug(f"LLM cache HIT: {prompt[:50]!r}")
            return _CachedResponse(cached)
        logger.debug(f"LLM cache MISS: {prompt[:50]!r}")
        result = self._fallback.complete(prompt, **kwargs)
        self._cache.set(actual_model, prompt, str(result))
        return result

    def __getattr__(self, name):
        return getattr(self._fallback, name)

    @property
    def model(self) -> str:
        return self._fallback.model

    @property
    def is_available(self) -> bool:
        return self._fallback.is_available


class _CachedResponse:
    """模拟 LLM 返回对象，使缓存命中时对上游透明。"""

    def __init__(self, text: str):
        self._text = text

    def __str__(self):
        return self._text

    def __repr__(self):
        return f"_CachedResponse({self._text[:50]!r}...)"


def get_llm() -> CachedLiteLLM:
    """获取全局 LLM 实例（LiteLLM 封装 + 缓存 + 多 Provider fallback）"""
    global _llm_instance
    if _llm_instance is None:
        settings = get_settings()
        _llm_instance = CachedLiteLLM(model=settings.LLM_MODEL, temperature=0.3)
    return _llm_instance


def get_active_provider() -> str:
    """返回当前活跃的 LLM provider（供健康检查）。"""
    global _active_provider
    return _active_provider

