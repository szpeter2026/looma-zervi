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
import time
import logging
import threading
from contextlib import asynccontextmanager

# 配置日志（在 import 其他模块之前）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
# 抑制 llama_index 和 httpx 的调试日志
logging.getLogger("llama_index").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# 必须在 import ollama / litellm 之前清掉代理
for _k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
    os.environ.pop(_k, None)

# 进程启动时间（供健康检查计算真实 uptime）
PROCESS_START_TIME = time.time()

# 基础设施就绪标志
pgvector_ready = False
llm_ready = False
embed_ready = False
rag_ready = False
llm_provider_active: str = ""
embed_provider_active: str = ""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from llama_index.core import Settings
from src.core.config import get_settings
from src.core.llm import get_llm, get_active_provider
from src.core.embeddings import get_embed_model, get_active_embed_provider
from src.retrieval.rag_engine import seed_knowledge, reset_index
from src.api.routes import system_router, ask_router, jobs_router, resume_router, auth_router, region_router, reports_router
from src.api.routes.web_panel import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时配置 LlamaIndex 全局 Settings，种子知识库在后台线程执行"""
    global pgvector_ready, llm_ready, embed_ready, rag_ready, llm_provider_active, embed_provider_active
    settings = get_settings()

    # LlamaIndex 全局配置 — Embedding
    try:
        Settings.embed_model = get_embed_model()
        embed_provider_active = get_active_embed_provider()
        if embed_provider_active != "unavailable":
            embed_ready = True
            logging.getLogger("looma").info(f"Embedding provider 已连接: {embed_provider_active}")
        else:
            logging.getLogger("looma").warning("所有 Embedding provider 均不可用")
    except Exception as e:
        logging.getLogger("looma").warning(f"Embedding 初始化失败: {e}")

    # LlamaIndex 全局配置 — LLM
    try:
        Settings.llm = get_llm()
        llm_provider_active = get_active_provider()
        llm_ready = Settings.llm.is_available
        if llm_ready:
            logging.getLogger("looma").info(f"LLM provider 已连接: {llm_provider_active}")
        else:
            logging.getLogger("looma").warning("所有 LLM provider 均不可用")
    except Exception as e:
        logging.getLogger("looma").warning(f"LLM 初始化失败: {e}")

    # 后台线程执行种子知识库（不阻塞服务启动）
    def _bg_seed():
        global pgvector_ready, rag_ready
        try:
            seed_knowledge()
            pgvector_ready = True
            rag_ready = True
            logging.getLogger("looma").info(f"种子知识库就绪 (schema={settings.SCHEMA})")
        except Exception as e:
            logging.getLogger("looma").warning(f"种子知识库初始化失败: {e}")

    threading.Thread(target=_bg_seed, daemon=True).start()

    yield
    logging.getLogger("looma").info("shutdown: 清理...")
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

# ---- 挂载静态文件（CSS / JS 等）----
# __file__ = src/api/app.py → 上 3 级到项目根目录
_static_dir = Path(__file__).resolve().parent.parent.parent / "web" / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="web_static")

# H5 用户端静态文件
_user_static_dir = Path(__file__).resolve().parent.parent.parent / "web" / "user" / "static"
if _user_static_dir.exists():
    app.mount("/user/static", StaticFiles(directory=str(_user_static_dir)), name="user_static")

# ---- 注册 API 路由 ----
app.include_router(system_router)
app.include_router(ask_router)
app.include_router(jobs_router)
app.include_router(resume_router)
app.include_router(auth_router)
app.include_router(region_router)
app.include_router(reports_router)

# ---- 注册 Web 面板路由（最后注册，避免覆盖 API）----
app.include_router(web_router)


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.LOOMA_HOST, port=settings.LOOMA_PORT)
