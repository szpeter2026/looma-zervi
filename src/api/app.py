"""Looma FastAPI 应用入口 — 底座优先，功能层组织

启动：
    uvicorn src.api.app:app --host 127.0.0.1 --port 8010 --reload

前置：
    - PG + pgvector 运行（docker-compose up -d 或本地安装）
    - Ollama 运行，qwen2.5-coder:1.5b + nomic-embed-text:latest 已 pull
    - .env 配置正确（参考 .env.example）
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

# 必须在 import ollama / litellm 之前清掉代理
for _k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
    os.environ.pop(_k, None)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llama_index.core import Settings
from src.core.config import get_settings
from src.core.llm import get_llm
from src.core.embeddings import get_embed_model
from src.retrieval.rag_engine import seed_knowledge, reset_index
from src.api.routes import system_router, ask_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时配置 LlamaIndex 全局 Settings + 种子知识库"""
    settings = get_settings()

    # LlamaIndex 全局配置
    Settings.embed_model = get_embed_model()
    Settings.llm = get_llm()

    # 种子知识库
    print(f"[startup] 种子知识库...", flush=True)
    seed_knowledge()
    print(f"[startup] 知识库就绪 (schema={settings.SCHEMA}, table={settings.TABLE})", flush=True)
    yield
    print("[shutdown] 清理...", flush=True)
    reset_index()


app = FastAPI(
    title="Looma & Zervi API",
    description="底座优先 — LlamaIndex + LiteLLM + FastAPI（对齐 api.yaml v1.1.0）",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(system_router)
app.include_router(ask_router)


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.LOOMA_HOST, port=settings.LOOMA_PORT)
