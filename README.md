# Looma & Zervi 融合项目

> Tatha + DemoPeter 融合的工程目录，按功能层组织。
> 决策依据：`docs/决策文档_底座优先修订版.md`（仓库外，原文档在桌面）
> 共享 API 契约：`docs/api.yaml`（Looma & Zervi Shared API Contract v1.1.0）

## 当前阶段：P1 底座五步 — 已关闭（2026-06-16）

底座优先路线实测可执行，铁证如下：

| 证据 | 耗时 | 验证了什么 |
|---|---|---|
| `smoke_pgvector.py` | 169ms | Step 1+2: 裸 psycopg + pgvector + 768d 余弦距离 |
| `smoke_llamaindex.py` | 231ms | Step 3: LlamaIndex + PGVectorStore 与裸 psycopg 排序一致 |
| `smoke_api.py` | 12677ms | Step 4+5: FastAPI /v1/ask + LiteLLM RAG 检索 + LLM 生成 |

| Step | 修订版要求 | 状态 |
|------|-----------|------|
| 1 | pgvector 唯一（PG 17 + pgvector 扩展） | done |
| 2 | 768d nomic-embed 统一 | done |
| 3 | LlamaIndex + PGVectorStore | done |
| 4 | LiteLLM (ollama/qwen2.5-coder:1.5b) | done |
| 5 | FastAPI /v1/ask 单入口（对齐 api.yaml v1.1.0） | done |

## 目录结构

```
looma-zervi/
├── src/                        # Looma Python 服务端（按功能层组织）
│   ├── core/                   # AI 核心层
│   │   ├── config.py           # 全局配置（.env 驱动）
│   │   ├── llm.py              # LiteLLM 统一调用
│   │   └── embeddings.py       # nomic-embed 768d 标准化
│   ├── retrieval/              # 检索层
│   │   ├── vector_store.py     # pgvector 统一接口
│   │   └── rag_engine.py       # LlamaIndex RAG 引擎
│   ├── api/                    # Web 层
│   │   ├── app.py              # FastAPI 入口
│   │   ├── models.py           # 请求/响应模型（对齐 api.yaml v1.1.0）
│   │   └── routes/             # 路由模块
│   │       ├── system.py       # /v1/health
│   │       └── ask.py          # /v1/ask
│   ├── agents/                 # 能力端口（P2）
│   ├── pipeline/               # 数据管道（P2）
│   └── db/                     # 数据层（P2）
├── zervi/                      # Zervi Rust 客户端
│   ├── Cargo.toml
│   └── src/main.rs             # reqwest + clap，调 Looma API
├── scripts/                    # 烟测脚本
│   ├── smoke_pgvector.py       # Step 1+2
│   ├── smoke_llamaindex.py     # Step 3
│   └── smoke_api.py            # Step 4+5
├── docs/
│   └── api.yaml                # 共享 API 契约 v1.1.0（唯一真理源）
├── tests/                      # 测试（P2）
├── docker-compose.yml          # pgvector 容器
├── .env.example                # 环境变量模板
├── requirements.txt
└── README.md
```

## 快速开始

### 1. 启动 pgvector 容器

```bash
docker compose up -d
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 PG 密码等配置
```

### 3. 安装 Python 依赖

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. 跑烟测

```bash
python scripts/smoke_pgvector.py
python scripts/smoke_llamaindex.py
python scripts/smoke_api.py
```

### 5. 启动开发服务器

```bash
uvicorn src.api.app:app --host 127.0.0.1 --port 8010 --reload
```

## 踩坑记录

| 坑 | 修法 |
|----|------|
| 沙箱代理让 ollama-py 卡死 | import 前 pop 6 个代理环境变量 |
| PGVectorStore.delete() 强制要 ref_doc_id | 用 psycopg 直接 TRUNCATE 兜底 |
| PGVectorStore._engine 是 None（懒加载） | 外连 psycopg 做清理 |
| ollama run 退出后模型从显存卸载 | 烟测前预热，或设置 keep_alive 参数 |
| LlamaIndex 0.14 要单独装 ollama embedder | `pip install llama-index-embeddings-ollama` |
| Ollama 冷启动 embeddings API 30s 不响应 | 烟测前 `ollama run` 一次预热，或加 keep_alive |

## 下一步（P2 业务功能自然生长）

- 文档导入管道（MarkItDown 解析 → 分块 → embedding → pgvector）
- 跨库检索（本地私有文档 ↔ 远程公共知识）
- 中央大脑意图路由（/v1/ask 自动分发到 rag/resume/jobs）
- Zervi 本地引擎（Rust + sqlx + pgvector + Ollama 本地推理）
- 接 DemoPeter 现有 RAG 面板
