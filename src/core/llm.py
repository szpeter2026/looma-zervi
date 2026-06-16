"""Looma core — LLM 统一调用（LiteLLM）"""
from __future__ import annotations

from llama_index.llms.litellm import LiteLLM
from src.core.config import get_settings


def get_llm() -> LiteLLM:
    """获取全局 LLM 实例（LiteLLM 封装）"""
    settings = get_settings()
    return LiteLLM(model=settings.LLM_MODEL, temperature=0.3)
