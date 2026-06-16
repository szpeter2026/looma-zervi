# Looma & Zervi 融合项目

> Tatha + DemoPeter 融合的工程目录。
> 决策依据：`/Users/jason/Projects/Tatha+DemoPeter_融合决策_底座优先修订版.md`。
> 共享 API 契约：`/Users/jason/Projects/api.yaml`（Looma & Zervi Shared API Contract v1.1.0）。

## 当前阶段：P1 底座五步 — ✅ 已关闭（2026-06-16）

底座优先路线在这台 Mac 上**实测可执行**，铁证如下：

| 证据 | 耗时 | 验证了什么 |
|---|---|---|
| `smoke_pgvector.py` | 169ms | Step 1+2: 裸 psycopg + pgvector + 768d 余弦距离 |
| `smoke_llamaindex.py` | 231ms | Step 3: LlamaIndex + PGVectorStore 与裸 psycopg 排序一致 |
| `smoke_api.py` | 12677ms | Step 4+5: FastAPI /v1/ask + LiteLLM RAG 检索 + LLM 生成 |

| Step | 修订版要求 | 状态 |
|------|-----------|------|
| 1 | pgvector 唯一（PG 17.9 + 0.8.0） | ✅ |
| 2 | 768d nomic-embed 统一 | ✅ |
| 3 | LlamaIndex + PGVectorStore | ✅ |
| 4 | LiteLLM (ollama/qwen2.5-coder:1.5b) | ✅ |
| 5 | FastAPI /v1/ask 单入口（对齐 api.yaml） | ✅ |

**关闭声明**：底座验证阶段到此为止。后续 P2 业务功能（文档导入、跨库检索、意图路由）直接在这个干净底座上**长**——不再为"验证"而验证。

## 目标（已达成）

验证"统一数据底座"不是纸面推演，是 **169ms + 231ms + 12s** 的实测数据；五个冲突维度全部在工程上消解，不是"延迟处理"。

## 目录结构

```
looma-zervi/
├── .venv → ~/.cache/looma-zervi/.venv   # 隔离的 Python 3.13.12 环境
├── app/
│   └── main.py                 # FastAPI 入口（/v1/ask + /v1/health），业务功能起点
├── scripts/
│   ├── smoke_pgvector.py       # Step 1+2 烟测（裸 psycopg + pgvector）
│   ├── smoke_llamaindex.py     # Step 3 烟测（LlamaIndex + pgvector）
│   └── smoke_api.py            # Step 4+5 烟测（FastAPI + LiteLLM）
├── docs/ tests/
├── requirements.txt
└── README.md
```

## 跑烟测

```bash
# Step 1+2: 裸 psycopg + pgvector
.venv/bin/python scripts/smoke_pgvector.py

# Step 3: LlamaIndex + pgvector
.venv/bin/python scripts/smoke_llamaindex.py

# Step 4+5: FastAPI + LiteLLM 全链路
.venv/bin/python scripts/smoke_api.py
```

## 启动开发服务器

```bash
cd /Users/jason/Projects/looma-zervi
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

## 踩坑记录（沉淀给后续 P2 业务开发）

| 坑 | 修法 |
|----|------|
| com.apple.provenance 标签让 pip install 写不进 .venv | venv 建在 `~/.cache/looma-zervi/.venv`，软链进工程 |
| 沙箱代理 `http_proxy=127.0.0.1:62081` 让 ollama-py 卡死 | import 前 pop 6 个代理环境变量 |
| PGVectorStore.delete() 强制要 ref_doc_id | 用 psycopg 直接 TRUNCATE 兜底 |
| PGVectorStore._engine 是 None（懒加载） | 外连 psycopg 做清理 |
| ollama run 退出后模型从显存卸载 | 烟测前预热，或设置 keep_alive 参数 |
| LlamaIndex 0.14 要单独装 ollama embedder | `pip install llama-index-embeddings-ollama` |
| Ollama 冷启动 embeddings API 30s 不响应 | 烟测前 `ollama run` 一次预热，或加 keep_alive |

## 下一步（P2 业务功能自然生长）

P1 底座关闭后，业务功能在这个干净底座上**长**：

- 文档导入管道（MarkItDown 解析 → 分块 → embedding → pgvector）
- 跨库检索（本地私有文档 ↔ 远程公共知识）
- 中央大脑意图路由（/v1/ask 自动分发到 rag/resume/jobs）
- 接 DemoPeter 现有 RAG 面板

> 这些**不是底座验证**，是产品功能。开始之前请确认底座五步无误，再启动 P2。
