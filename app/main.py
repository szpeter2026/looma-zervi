"""
looma-zervi FastAPI 入口 — 底座优先 Step 4+5 最小闭环
=====================================================
验证：
- LiteLLM 统一模型调用（ollama/qwen2.5-coder:1.5b）
- FastAPI /v1/ask 单入口（对齐 api.yaml 契约）
- LlamaIndex PGVectorStore + nomic-embed 检索 → LLM 生成回答

启动：
    cd /Users/jason/Projects/looma-zervi
    .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload

前置：
    - ServBay PG 运行 @ 127.0.0.1:5432
    - ServBay Ollama 运行 @ 127.0.0.1:11434
    - qwen2.5-coder:1.5b + nomic-embed-text:latest 已 pull
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

# 必须在 import ollama / litellm 之前清掉代理
for _k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
    os.environ.pop(_k, None)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.llms.litellm import LiteLLM

# ---- 配置 ----
PG_DSN = "postgresql://jason:ServBay.dev@127.0.0.1:5432/postgres"
OLLAMA_HOST = "http://127.0.0.1:11434"
EMBED_MODEL = "nomic-embed-text:latest"
LLM_MODEL = "ollama/qwen2.5-coder:1.5b"
DIM = 768
SCHEMA = "looma"
TABLE = "knowledge"

# ---- 全局 LlamaIndex 配置 ----
Settings.embed_model = OllamaEmbedding(
    model_name=EMBED_MODEL,
    base_url=OLLAMA_HOST,
    ollama_additional_kwargs={"dim": DIM},
)
Settings.llm = LiteLLM(model=LLM_MODEL, temperature=0.3)

# 全局 VectorStore + Index（懒加载）
_vector_store: PGVectorStore | None = None
_index: VectorStoreIndex | None = None


def _get_vector_store() -> PGVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = PGVectorStore.from_params(
            host="127.0.0.1",
            port=5432,
            user="jason",
            password="ServBay.dev",
            database="postgres",
            table_name=TABLE,
            schema_name=SCHEMA,
            embed_dim=DIM,
            hnsw_kwargs={"m": 16, "ef_construction": 64},
        )
    return _vector_store


def _seed_knowledge():
    """种子知识库：写入几条常识数据，确保检索有内容可查"""
    import psycopg as _psycopg

    # 幂等：表存在就清空重建
    with _psycopg.connect(PG_DSN, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s;",
                (SCHEMA, TABLE),
            )
            if cur.fetchone():
                cur.execute(f"TRUNCATE TABLE {SCHEMA}.{TABLE} RESTART IDENTITY;")

    docs = [
        Document(text="Looma 是一个 AI 驱动的职业发展平台，包含简历解析、职位匹配、MBTI 测评等功能。"),
        Document(text="Zervi 是 Looma 的客户端应用，支持本地优先架构，用户私有文档存储在本地 pgvector。"),
        Document(text="底座优先架构：统一向量引擎为 pgvector，统一嵌入模型为 nomic-embed-text 768d，统一检索框架为 LlamaIndex。"),
        Document(text="修订版路线五步：pgvector → nomic-embed → LlamaIndex → LiteLLM → FastAPI。"),
        Document(text="向量检索使用余弦相似度（<=> 操作符），支持 HNSW 索引加速百万级向量查询。"),
        Document(text="LiteLLM 统一所有模型调用，支持 Ollama 本地模型和 DeepSeek 云端模型无缝切换。"),
    ]
    vs = _get_vector_store()
    index = VectorStoreIndex.from_documents(docs, vector_store=vs, show_progress=False)
    return index


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时种子知识库，关闭时清理"""
    global _index
    print(f"[startup] 种子知识库...", flush=True)
    _index = _seed_knowledge()
    print(f"[startup] 知识库就绪 (schema={SCHEMA}, table={TABLE})", flush=True)
    yield
    print("[shutdown] 清理...", flush=True)


app = FastAPI(
    title="Looma & Zervi API",
    description="底座优先最小闭环 — LlamaIndex + LiteLLM + FastAPI",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- 请求/响应模型（对齐 api.yaml） ----

class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    context_scope: str = Field(default="public", pattern="^(private|public|both)$")


class AskResponse(BaseModel):
    answer: str
    intent: str = "rag"
    sources: list[dict] = []
    tokens_used: int = 0


# ---- 路由 ----

@app.get("/v1/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "uptime_seconds": int(time.time())}


@app.post("/v1/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """免费体验单入口：RAG 检索 + LLM 生成回答"""
    if _index is None:
        raise HTTPException(status_code=503, detail="知识库未就绪")

    t0 = time.time()

    # 1. 检索 top-3
    query_engine = _index.as_query_engine(similarity_top_k=3)
    response = await query_engine.aquery(req.query)

    # 2. 收集来源
    sources = []
    for node in response.source_nodes:
        sources.append({
            "text": node.text[:200],
            "score": round(node.score, 4) if node.score else None,
        })

    elapsed = int((time.time() - t0) * 1000)
    return AskResponse(
        answer=str(response),
        intent="rag",
        sources=sources,
        tokens_used=elapsed,  # 简化：用耗时代理（实际应用应统计 token）
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8010)
