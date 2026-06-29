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

    @property
    def is_production(self):
        return self.FLASK_ENV == "production"


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
