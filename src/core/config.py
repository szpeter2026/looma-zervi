"""Looma core — 配置与环境变量"""
from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# 加载 .env（从项目根目录），再加载 .env.local（覆盖同名变量）
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")
_local_env = _project_root / ".env.local"
if _local_env.exists():
    load_dotenv(_local_env, override=True)


class Settings:
    """全局配置，全部从环境变量读取"""

    # ---- 数据库 ----
    PG_HOST: str = os.getenv("PG_HOST", "127.0.0.1")
    PG_PORT: int = int(os.getenv("PG_PORT", "5432"))
    PG_USER: str = os.getenv("PG_USER", "postgres")
    PG_PASSWORD: str = os.getenv("PG_PASSWORD", "postgres")
    PG_DATABASE: str = os.getenv("PG_DATABASE", "looma")

    # ---- Ollama ----
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    EMBED_MODEL: str = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "ollama/qwen2.5-coder:1.5b")
    EMBED_DIM: int = int(os.getenv("EMBED_DIM", "768"))

    # ---- 多 Provider 优先级（逗号分隔，按优先级尝试）----
    # 值为 provider 名称列表，例如："deepseek,ollama,openai"
    LLM_PROVIDER_ORDER: str = os.getenv("LLM_PROVIDER_ORDER", "ollama,deepseek,openai")

    # Embedding provider 优先级（独立于 LLM provider）
    EMBED_PROVIDER_ORDER: str = os.getenv("EMBED_PROVIDER_ORDER", "ollama,openai,deepseek")

    # 可选：为每个 embedding provider 指定 model 名称
    OPENAI_EMBED_MODEL: str = os.getenv("OPENAI_EMBED_MODEL", "")
    DEEPSEEK_EMBED_MODEL: str = os.getenv("DEEPSEEK_EMBED_MODEL", "")

    # 可选：为每个 provider 指定默认 model 名称（若未设置则使用 LLM_MODEL）
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "")

    # ---- API Keys（按需配置，不配则跳过对应 provider）----
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")  # 可自定义 API 代理地址

    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "")

    # ---- 服务 ----
    LOOMA_HOST: str = os.getenv("LOOMA_HOST", "127.0.0.1")
    LOOMA_PORT: int = int(os.getenv("LOOMA_PORT", "8010"))

    # ---- PG 默认 schema/table ----
    SCHEMA: str = "looma"
    TABLE: str = "knowledge"

    # ---- 认证（P2 实现）----
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

    # ---- 对象存储（P2 实现）----
    S3_ENDPOINT: str = os.getenv("S3_ENDPOINT", "")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "looma-uploads")

    @property
    def PG_DSN(self) -> str:
        return f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

