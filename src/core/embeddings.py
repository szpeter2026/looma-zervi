"""Looma core — Embedding 统一抽象（多 Provider fallback + 重试/熔断）

支持 provider（按 EMBED_PROVIDER_ORDER 优先级）:
  - ollama: nomic-embed-text (768d)  — 本地默认
  - openai: text-embedding-3-small / text-embedding-ada-002
  - deepseek: deepseek-embedding

当主 provider 不可用时会自动切换到下一个，确保 RAG 链路不会因 Ollama down 而阻断。
每次调用内置超时 + 指数退避重试 + 熔断保护。
"""

from __future__ import annotations

import concurrent.futures
import logging
import time
import urllib.request
from typing import Optional

from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from src.core.config import get_settings
from src.core.resilience import (
    get_embed_circuit_breaker,
    EMBED_CALL_TIMEOUT,
    EMBED_MAX_RETRIES,
)

logger = logging.getLogger("looma.embed")

# 当前活跃的 embedding provider
_active_embed_provider: str = ""


class _FallbackEmbedding(BaseEmbedding):
    """多 Provider fallback embedding：按优先级尝试初始化，调用失败自动切换。"""

    _embed_model: BaseEmbedding | None = None
    _current_provider: str = ""
    _current_model: str = ""
    _provider_idx: int = 0
    _providers: list[str] = []
    _temperature: float = 0.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        global _active_embed_provider
        settings = get_settings()
        # provider 优先级列表
        order = getattr(settings, "EMBED_PROVIDER_ORDER", "ollama,openai,deepseek")
        self._providers = [p.strip().lower() for p in order.split(",") if p.strip()]
        self._provider_idx = 0
        self._try_next_provider()
        _active_embed_provider = self._current_provider or "unavailable"

    # ── BaseEmbedding 要求的抽象方法 ──

    @classmethod
    def class_name(cls) -> str:
        return "FallbackEmbedding"

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._call_embed(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._call_embed(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._call_embed(text)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._call_embed(text)

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self._call_embed(t) for t in texts]

    # ── 核心调用逻辑（重试 + 熔断 + 超时）──

    def _call_embed(self, text: str) -> list[float]:
        """带重试、熔断、超时的 embedding 调用。"""
        cb = get_embed_circuit_breaker()

        # 熔断检查
        if not cb.allow_request():
            raise RuntimeError(f"Embedding 熔断器已断开（{cb.stats()['failure_count']} 次连续失败），拒绝请求")

        # 检查当前 provider 是否可用
        if self._embed_model is None:
            if not self._try_next_provider():
                raise RuntimeError("无可用的 Embedding provider")

        last_exception = None
        for attempt in range(EMBED_MAX_RETRIES + 1):
            try:
                # 带超时调用
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._embed_model.get_text_embedding, text)
                    result = future.result(timeout=EMBED_CALL_TIMEOUT)

                # 成功
                cb.record_success()
                return result

            except concurrent.futures.TimeoutError:
                last_exception = TimeoutError(f"Embedding {self._current_provider} 调用超时 ({EMBED_CALL_TIMEOUT}s)")
                cb.record_failure()
                logger.warning(
                    f"Embedding {self._current_provider} 超时 (attempt {attempt + 1}/{EMBED_MAX_RETRIES + 1})"
                )
            except Exception as e:
                last_exception = e
                cb.record_failure()
                logger.warning(
                    f"Embedding {self._current_provider} 调用失败 (attempt {attempt + 1}/{EMBED_MAX_RETRIES + 1}): {e}"
                )

            # 退避等待后重试
            if attempt < EMBED_MAX_RETRIES:
                delay = 0.5 * (2 ** attempt)
                logger.info(f"Embedding 重试等待 {delay:.1f}s...")
                time.sleep(delay)

            # 最后一次尝试失败后，尝试切换 provider
            if attempt == EMBED_MAX_RETRIES:
                logger.warning(f"Embedding {self._current_provider} 全部重试失败，尝试下一个 provider")
                if self._try_next_provider():
                    logger.info(f"已切换到 embedding provider: {self._current_provider}")
                    try:
                        result = self._embed_model.get_text_embedding(text)
                        cb.record_success()
                        return result
                    except Exception as e2:
                        last_exception = e2
                        cb.record_failure()
                        logger.error(f"新 embedding provider {self._current_provider} 也调用失败: {e2}")

        raise last_exception or RuntimeError("Embedding 调用失败")

    # ── provider 检测与初始化 ──

    def _check_ollama(self, settings) -> bool:
        try:
            url = settings.OLLAMA_HOST.rstrip("/") + "/v1/models"
            with urllib.request.urlopen(url, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _try_next_provider(self) -> bool:
        global _active_embed_provider
        settings = get_settings()

        while self._provider_idx < len(self._providers):
            prov = self._providers[self._provider_idx]
            self._provider_idx += 1

            try:
                if prov == "ollama":
                    if not self._check_ollama(settings):
                        logger.warning("Ollama 不可达，跳过 embedding provider")
                        continue
                    model_name = settings.EMBED_MODEL
                    self._embed_model = OllamaEmbedding(
                        model_name=model_name,
                        base_url=settings.OLLAMA_HOST,
                        ollama_additional_kwargs={"dim": settings.EMBED_DIM},
                    )
                    self._current_provider = "ollama"
                    self._current_model = model_name
                    logger.info(f"Embedding provider 已连接: ollama -> {model_name}")
                elif prov == "openai":
                    key = settings.OPENAI_API_KEY
                    if not key:
                        logger.warning("未配置 OPENAI_API_KEY，跳过 OpenAI embedding")
                        continue
                    model_name = getattr(settings, "OPENAI_EMBED_MODEL", "") or "text-embedding-3-small"
                    base_url = settings.OPENAI_BASE_URL or None
                    self._embed_model = OpenAIEmbedding(
                        model=model_name,
                        api_key=key,
                        api_base=base_url,
                        dimensions=settings.EMBED_DIM if model_name == "text-embedding-3-small" else None,
                    )
                    self._current_provider = "openai"
                    self._current_model = model_name
                    logger.info(f"Embedding provider 已连接: openai -> {model_name}")
                elif prov == "deepseek":
                    key = settings.DEEPSEEK_API_KEY
                    if not key:
                        logger.warning("未配置 DEEPSEEK_API_KEY，跳过 DeepSeek embedding")
                        continue
                    model_name = getattr(settings, "DEEPSEEK_EMBED_MODEL", "") or "deepseek-chat"
                    base_url = settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com/v1"
                    # DeepSeek 的 embedding 通过 OpenAI 兼容 API 暴露
                    self._embed_model = OpenAIEmbedding(
                        model=model_name,
                        api_key=key,
                        api_base=base_url,
                        dimensions=settings.EMBED_DIM,
                    )
                    self._current_provider = "deepseek"
                    self._current_model = model_name
                    logger.info(f"Embedding provider 已连接: deepseek -> {model_name}")
                else:
                    logger.warning(f"未知 embedding provider: {prov}，跳过")
                    continue

                _active_embed_provider = self._current_provider
                return True

            except Exception as e:
                logger.warning(f"Embedding provider {prov} 初始化失败: {e}")
                self._embed_model = None
                continue

        logger.error("所有 Embedding provider 均不可用")
        _active_embed_provider = "unavailable"
        return False

    # ── 属性代理 ──

    @property
    def model(self) -> str:
        return self._current_model

    @property
    def provider(self) -> str:
        return self._current_provider

    @property
    def is_available(self) -> bool:
        return self._embed_model is not None


def get_embed_model() -> _FallbackEmbedding:
    """获取全局 Embedding 模型实例（多 provider fallback）"""
    return _FallbackEmbedding()


def get_active_embed_provider() -> str:
    """返回当前活跃的 embedding provider（供健康检查）。"""
    global _active_embed_provider
    return _active_embed_provider
