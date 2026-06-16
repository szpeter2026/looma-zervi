"""
looma-zervi / 底座优先 P0 烟测
============================
端到端验证：在 ServBay PG17 + pgvector 0.8.0 上跑通 768d 向量存取。
链路：Ollama nomic-embed-text -> psycopg3 -> pgvector -> 余弦相似度

输出格式：阶段 + 耗时 + 状态，让 Jason 几秒能看懂跑没跑通。
"""
from __future__ import annotations

import os
import time
import json
import sys
from pathlib import Path

import ollama
import psycopg

# ---- 全部配置在顶部，方便改 ----
PG_DSN = "postgresql://jason:ServBay.dev@127.0.0.1:5432/postgres"
OLLAMA_HOST = "http://127.0.0.1:11434"  # ServBay Ollama 默认监听
EMBED_MODEL = "nomic-embed-text:latest"
DIM = 768
SCHEMA = "smoke"
TABLE = "docs"
STATE_FILE = Path(__file__).resolve().parent.parent / ".smoke_state.json"

# 三段测试文本：一组相关（pgvector/底座）、一组不相关（做饭）
SAMPLES = [
    "pgvector 已经在 ServBay 上跑通 768d 相似度检索",
    "底座优先：统一向量引擎到 pgvector，淘汰 FAISS 和 Chroma",
    "修订版路线：pgvector + nomic-embed + LlamaIndex + LiteLLM + FastAPI",
    "今天晚上做个西红柿炒蛋，配米饭",
]


def step(msg: str) -> None:
    print(f"\n=== {msg} ===", flush=True)


def main() -> int:
    started = time.time()
    state: dict = {"started_at": time.time(), "steps": {}}

    # 0. 客户端连接
    step("0. 连接 Ollama + PG")
    t0 = time.time()
    ollama_client = ollama.Client(host=OLLAMA_HOST)
    pg = psycopg.connect(PG_DSN, autocommit=True)
    with pg.cursor() as cur:
        cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector';")
        ver = cur.fetchone()[0]
    state["steps"]["connect"] = {
        "ollama": OLLAMA_HOST,
        "pgvector": ver,
        "elapsed_ms": int((time.time() - t0) * 1000),
    }
    print(f"  PG pgvector 扩展版本: {ver}")
    print(f"  Ollama endpoint:      {OLLAMA_HOST}")

    # 1. 准备 schema 和表（幂等）
    step("1. 准备 schema + 表（幂等）")
    t0 = time.time()
    with pg.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")
        cur.execute(f"DROP TABLE IF EXISTS {SCHEMA}.{TABLE};")
        cur.execute(
            f"""
            CREATE TABLE {SCHEMA}.{TABLE} (
                id        bigserial PRIMARY KEY,
                content   text NOT NULL,
                embedding vector({DIM}) NOT NULL
            );
            """
        )
    state["steps"]["schema"] = {"dim": DIM, "elapsed_ms": int((time.time() - t0) * 1000)}

    # 2. 嵌入并写入
    step(f"2. Ollama 嵌入 {len(SAMPLES)} 条文本（{EMBED_MODEL}）")
    t0 = time.time()
    rows = []
    for i, text in enumerate(SAMPLES, 1):
        t_emb = time.time()
        resp = ollama_client.embeddings(model=EMBED_MODEL, prompt=text)
        vec = resp["embedding"]
        assert len(vec) == DIM, f"维度不对：{len(vec)} ≠ {DIM}"
        rows.append((text, vec))
        print(f"  [{i}/{len(SAMPLES)}] dim={len(vec)}  {time.time()-t_emb:.2f}s  {text[:30]}")
    state["steps"]["embed"] = {
        "model": EMBED_MODEL, "count": len(rows),
        "elapsed_ms": int((time.time() - t0) * 1000),
    }

    t0 = time.time()
    with pg.cursor() as cur:
        for text, vec in rows:
            cur.execute(
                f"INSERT INTO {SCHEMA}.{TABLE} (content, embedding) VALUES (%s, %s::vector);",
                (text, vec),
            )
    state["steps"]["insert"] = {"elapsed_ms": int((time.time() - t0) * 1000)}

    # 3. 余弦相似度检索
    step("3. 用第 1 条做 query，查最相似的 top-3")
    t0 = time.time()
    query_text = SAMPLES[0]
    qvec = ollama_client.embeddings(model=EMBED_MODEL, prompt=query_text)["embedding"]
    with pg.cursor() as cur:
        cur.execute(
            f"""
            SELECT id, content, embedding <=> %s::vector AS dist
            FROM {SCHEMA}.{TABLE}
            ORDER BY embedding <=> %s::vector
            LIMIT 3;
            """,
            (qvec, qvec),
        )
        results = cur.fetchall()
    state["steps"]["query"] = {"elapsed_ms": int((time.time() - t0) * 1000)}

    print(f"  query: {query_text}")
    for rid, content, dist in results:
        print(f"    #{rid}  dist={dist:.4f}  {content}")

    # 4. 校验：最相似的应该是 query 自身（dist=0）
    step("4. 校验：最相似项应当是 query 自身（dist=0）")
    top_id, top_content, top_dist = results[0]
    if top_id == 1 and top_dist < 1e-6:
        verdict = "PASS"
        print(f"  ✅ PASS  dist={top_dist:.6f}")
    else:
        verdict = "FAIL"
        print(f"  ❌ FAIL  expected id=1, got id={top_id} dist={top_dist}")

    # 5. 清理
    step("5. 清理（drop schema）")
    with pg.cursor() as cur:
        cur.execute(f"DROP SCHEMA {SCHEMA} CASCADE;")

    state["verdict"] = verdict
    state["total_ms"] = int((time.time() - started) * 1000)

    # 状态文件
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    print(f"\n=== 状态写入 {STATE_FILE.name}  总耗时 {state['total_ms']}ms ===")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ EXCEPTION: {type(e).__name__}: {e}", file=sys.stderr)
        raise
