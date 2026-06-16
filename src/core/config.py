"""Looma core — 配置与环境变量"""
from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# 加载 .env（从项目根目录）
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


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
