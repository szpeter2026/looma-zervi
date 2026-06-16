"""
smoke_llamaindex.py — LlamaIndex + pgvector 烟测
==============================================
验证：
1. LlamaIndex PGVectorStore 能连 PG + pgvector
2. nomic-embed-text:latest（Ollama）能正常产出 768d embedding
3. VectorStoreIndex 构建 + 相似度查询 正常
4. 结果与裸 psycopg 烟测（smoke_pgvector.py）排序一致

前置：
    - PG + pgvector 运行（docker-compose up -d 或本地安装）
    - Ollama 运行，nomic-embed-text:latest 已 pull
    - .env 配置正确（参考 .env.example）
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# LlamaIndex 核心
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.vector_stores.types import VectorStoreQueryMode

# ---- 配置全部从环境变量读取 ----
PG_HOST = os.getenv("PG_HOST", "127.0.0.1")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_DATABASE = os.getenv("PG_DATABASE", "looma")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text:latest")
DIM = int(os.getenv("EMBED_DIM", "768"))

PG_DSN = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

SCHEMA = "smoke_lili"
TABLE = "llama_docs"

STATE_FILE = Path(__file__).resolve().parent.parent / ".smoke_state_llamaindex.json"

# 与 smoke_pgvector.py 相同的测试文本
SAMPLES = [
    "pgvector 已经跑通 768d 相似度检索",
    "底座优先：统一向量引擎到 pgvector，淘汰 FAISS 和 Chroma",
    "修订版路线：pgvector + nomic-embed + LlamaIndex + LiteLLM + FastAPI",
    "今天晚上做个西红柿炒蛋，配米饭",
]


def step(msg: str) -> None:
    print(f"\n=== {msg} ===", flush=True)


def main() -> int:
    t0_all = time.time()
    state: dict = {"steps": {}, "queries": []}

    # 0. 配置 LlamaIndex 全局 Settings
    step("0. 配置 LlamaIndex Settings（OllamaEmbedding + pgvector）")
    t0 = time.time()
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_HOST,
        ollama_additional_kwargs={"dim": DIM},
    )
    Settings.llm = None
    state["steps"]["settings"] = {
        "embed_model": EMBED_MODEL,
        "ollama_url": OLLAMA_HOST,
        "dim": DIM,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }
    print(f"  embed_model={EMBED_MODEL}")
    print(f"  ollama_url={OLLAMA_HOST}")

    # 1. 构建 PGVectorStore（会自动建表 if not exists）
    step("1. 连接 PGVectorStore（自动建 schema + 表）")
    t0 = time.time()
    vector_store = PGVectorStore.from_params(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        database=PG_DATABASE,
        table_name=TABLE,
        schema_name=SCHEMA,
        embed_dim=DIM,
        hnsw_kwargs={"m": 16, "ef_construction": 64},
    )
    state["steps"]["pgvector_store"] = {
        "schema": SCHEMA,
        "table": TABLE,
        "dim": DIM,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }
    print(f"  schema={SCHEMA}, table={TABLE}")

    # 2. 删除旧数据（幂等）
    step("2. 清理旧数据（TRUNCATE）")
    t0 = time.time()
    try:
        import psycopg as _psycopg
        with _psycopg.connect(PG_DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"TRUNCATE TABLE {SCHEMA}.{TABLE} RESTART IDENTITY;"
                )
        print("  已清空旧数据")
    except Exception as e:
        print(f"  （无需清理：{e}）")
    state["steps"]["cleanup"] = {"elapsed_ms": int((time.time() - t0) * 1000)}

    # 3. 构建 Document 列表并插入
    step(f"3. 插入 {len(SAMPLES)} 条 Document（触发 Ollama embedding）")
    t0 = time.time()
    docs = [Document(text=t) for t in SAMPLES]
    index = VectorStoreIndex.from_documents(
        docs,
        vector_store=vector_store,
        show_progress=True,
    )
    state["steps"]["insert"] = {
        "count": len(docs),
        "elapsed_ms": int((time.time() - t0) * 1000),
    }
    print(f"  插入完成，耗时 {state['steps']['insert']['elapsed_ms']}ms")

    # 4. 相似度查询（与裸 psycopg 烟测相同的 query）
    step("4. 相似度查询（与 smoke_pgvector.py 相同 query）")
    t0 = time.time()
    query_engine = index.as_query_engine(
        similarity_top_k=3,
        vector_store_query_mode=VectorStoreQueryMode.DEFAULT,
    )
    query_text = SAMPLES[0]
    response = query_engine.query(query_text)
    state["steps"]["query"] = {
        "query": query_text,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }

    print(f"  query: {query_text}")
    print(f"  检索到的源文档：")
    results = []
    for i, node in enumerate(response.source_nodes, 1):
        score = node.score if node.score is not None else -1.0
        text = node.text[:60]
        results.append({"rank": i, "score": round(score, 4), "text": text})
        print(f"    #{i}  score={score:.4f}  {text}")

    # 5. 校验：排序应与裸 psycopg 烟测一致
    step("5. 校验：排序应与 smoke_pgvector.py 一致")
    top_text = results[0]["text"]
    if top_text.startswith(SAMPLES[0][:20]):
        verdict = "PASS"
        print(f"  PASS  #1={top_text[:30]}")
    else:
        verdict = "WARN"
        print(f"  WARN  #1 预期 '{SAMPLES[0][:20]}...' 实际 '{top_text[:30]}'")

    # 6. 清理
    step("6. 清理（TRUNCATE）")
    import psycopg as _psycopg
    with _psycopg.connect(PG_DSN, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s;",
                (SCHEMA,),
            )
            if cur.fetchone():
                cur.execute(f"TRUNCATE TABLE {SCHEMA}.{TABLE} RESTART IDENTITY;")
                print("  已清空测试数据")
            else:
                print(f"  schema {SCHEMA} 不存在，跳过清理")

    # 写状态文件
    state["verdict"] = verdict
    state["total_ms"] = int((time.time() - t0_all) * 1000)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    print(f"\n=== 状态写入 {STATE_FILE.name}  总耗时 {state['total_ms']}ms ===")
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nEXCEPTION: {type(e).__name__}: {e}", file=sys.stderr)
        raise
