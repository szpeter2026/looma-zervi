"""
Configuration management.
All secrets come from environment variables, never hardcoded.
Uses class-level __dict__ overrides so Flask's from_object()
always picks up the latest env values (not cached at import time).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Flask config that reads env vars dynamically.

    Flask's ``app.config.from_object()`` iterates over the class's
    ``__dict__`` and copies UPPER-case keys.  By storing them as
    descriptors (or just relying on ``os.getenv`` at access time),
    we ensure each ``from_object`` call gets fresh values.
    """

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret-change-me")
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    # WeChat
    WECHAT_APPID = os.getenv("WECHAT_APPID", "")
    WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
    WECHAT_DEV_MODE = os.getenv("WECHAT_DEV_MODE", "false").lower() == "true"

    # DeepSeek
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # ChromaDB
    CHROMA_MODE = os.getenv("CHROMA_MODE", "local")
    CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")
    CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "looma_knowledge")

    # SQLite — must be dynamic so tests can override per-fixture
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/looma.db")

    # CORS
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174"
    ).split(",")

    # Quota
    FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "30"))

    # LLM Provider (multi-provider fallback: deepseek, ollama, openai)
    LLM_PROVIDER_ORDER = os.getenv("LLM_PROVIDER_ORDER", "deepseek,ollama,openai")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")

    # Embedding provider
    EMBED_PROVIDER_ORDER = os.getenv("EMBED_PROVIDER_ORDER", "ollama,deepseek")
    EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")
    EMBED_DIM = int(os.getenv("EMBED_DIM", "768"))

    # API timeout
    API_REQUEST_TIMEOUT = float(os.getenv("API_REQUEST_TIMEOUT", "90.0"))

    # pgvector (optional — used by RAG engine if configured)
    PG_HOST = os.getenv("PG_HOST", "127.0.0.1")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_USER = os.getenv("PG_USER", "postgres")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
    PG_DATABASE = os.getenv("PG_DATABASE", "looma")

    # Navigator psychology layer
    PSYCHOLOGY_ENABLED = os.getenv("PSYCHOLOGY_ENABLED", "true").lower() == "true"
    PSYCHOLOGY_API_TYPE = os.getenv("PSYCHOLOGY_API_TYPE", "local")
    SENTINO_API_KEY = os.getenv("SENTINO_API_KEY", "")

    @property
    def is_production(self):
        return self.FLASK_ENV == "production"

    @property
    def PG_DSN(self):
        return (
            f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}"
            f"@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
        )


def _refresh_config():
    """Re-read all env vars into Config class attributes.

    Call this before ``app.config.from_object(Config)`` so that
    runtime env-var changes (e.g. per-test DATABASE_PATH overrides)
    are picked up instead of stale import-time values.
    """
    Config.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    Config.FLASK_ENV = os.getenv("FLASK_ENV", "development")
    Config.JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret-change-me")
    Config.JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    Config.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    Config.WECHAT_APPID = os.getenv("WECHAT_APPID", "")
    Config.WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
    Config.WECHAT_DEV_MODE = os.getenv("WECHAT_DEV_MODE", "false").lower() == "true"
    Config.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    Config.DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    Config.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    Config.CHROMA_MODE = os.getenv("CHROMA_MODE", "local")
    Config.CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
    Config.CHROMA_PORT = os.getenv("CHROMA_PORT", "8000")
    Config.CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "looma_knowledge")
    Config.DATABASE_PATH = os.getenv("DATABASE_PATH", "data/looma.db")
    Config.CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174"
    ).split(",")
    Config.FREE_DAILY_LIMIT = int(os.getenv("FREE_DAILY_LIMIT", "30"))
    Config.LLM_PROVIDER_ORDER = os.getenv("LLM_PROVIDER_ORDER", "deepseek,ollama,openai")
    Config.OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    Config.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
    Config.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    Config.OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
    Config.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")
    Config.EMBED_PROVIDER_ORDER = os.getenv("EMBED_PROVIDER_ORDER", "ollama,deepseek")
    Config.EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")
    Config.EMBED_DIM = int(os.getenv("EMBED_DIM", "768"))
    Config.API_REQUEST_TIMEOUT = float(os.getenv("API_REQUEST_TIMEOUT", "90.0"))
    Config.PG_HOST = os.getenv("PG_HOST", "127.0.0.1")
    Config.PG_PORT = int(os.getenv("PG_PORT", "5432"))
    Config.PG_USER = os.getenv("PG_USER", "postgres")
    Config.PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
    Config.PG_DATABASE = os.getenv("PG_DATABASE", "looma")
    Config.PSYCHOLOGY_ENABLED = os.getenv("PSYCHOLOGY_ENABLED", "true").lower() == "true"
    Config.PSYCHOLOGY_API_TYPE = os.getenv("PSYCHOLOGY_API_TYPE", "local")
    Config.SENTINO_API_KEY = os.getenv("SENTINO_API_KEY", "")
