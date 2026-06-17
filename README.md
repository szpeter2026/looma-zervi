# Looma & Zervi 融合项目

> Tatha + DemoPeter 融合的工程目录，按功能层组织。
> 决策依据：`docs/决策文档_底座优先修订版.md`（仓库外，原文档在桌面）
> 共享 API 契约：`docs/api.yaml`（Looma & Zervi Shared API Contract v1.1.0）

## 当前阶段：P1 底座五步 + 弹性优化 — 已关闭（2026-06-17）

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
| 6 | 业务模块迁移（Tatha + DemoPeter 全量模块 → looma-zervi） | done |
| 7 | Zervi Rust 客户端完整升级（P1 骨架 → 全端点 CLI） | done |
| 8 | **LLM 多 Provider fallback** (ollama→deepseek→openai) | done |
| 9 | **Embedding 多 Provider fallback** (ollama→openai→deepseek) | done |
| 10 | **调用弹性策略**（超时/重试/熔断） | done |
| 11 | **两层缓存**（LLM prompt 级 + 请求结果级） | done |
| 12 | **集成 Smoke 测试** | done |

## 目录结构

```
looma-zervi/
├── src/                           # Looma Python 服务端（按功能层组织）
│   ├── core/                      # AI 核心层
│   │   ├── config.py              # 全局配置（.env 驱动）
│   │   ├── llm.py                 # LiteLLM 统一调用（多 Provider + 缓存 + 重试/熔断）
│   │   ├── llm_cache.py           # LLM prompt 级缓存（TTL + LRU）
│   │   ├── embeddings.py          # Embedding 抽象（多 Provider fallback + 重试/熔断）
│   │   └── resilience.py          # 调用弹性策略（超时/重试/熔断器）
│   ├── retrieval/                 # 检索层
│   │   ├── vector_store.py        # pgvector 统一接口
│   │   └── rag_engine.py          # LlamaIndex RAG 引擎
│   ├── api/                       # Web 层
│   │   ├── app.py                 # FastAPI 入口
│   │   ├── models.py              # 请求/响应模型（对齐 api.yaml v1.1.0）
│   │   ├── auth.py                # 认证（Supabase JWT + Stub）
│   │   ├── quota.py               # 三档配额控制
│   │   └── routes/                # 路由模块
│   │       ├── system.py          # /v1/health（含 provider/cache/resilience 状态）
│   │       ├── ask.py             # /v1/ask（中央大脑单入口 + 请求级缓存）
│   │       ├── jobs.py            # /v1/jobs/match（职位匹配）
│   │       ├── resume.py          # /v1/resume/parse（简历解析）
│   │       ├── auth_routes.py     # /v1/auth/*（注册/登录/配额）
│   │       ├── region.py          # /v1/region（地区定价）
│   │       └── reports.py         # /v1/reports（报告生成）
│   ├── agents/                    # AI 能力端口
│   │   ├── central_brain.py       # 中央大脑（LLM 意图解析 + 8 意图分发）
│   │   ├── document_agents.py     # PydanticAI 文档解读（简历/征信）
│   │   ├── mbti_analyzer.py       # MBTI 人格测评
│   │   ├── mbti_career_match.py   # MBTI 职业匹配
│   │   └── poetry_search.py       # 诗词向量检索（pgvector 后端）
│   ├── pipeline/                  # 数据管道
│   │   ├── job_match_pipeline.py # 职位匹配流水线
│   │   ├── job_scoring.py         # LLM 多维打分（钱多事少离家近）
│   │   ├── job_schemas.py         # 职位/匹配 Pydantic 模型
│   │   └── report_gen.py          # 日/周/月报告生成器
│   └── db/                        # 数据层
│       └── manager.py             # SQLite 元数据库（文档/用户/配额）
├── zervi/                         # Zervi Rust 客户端
├── scripts/                       # 烟测脚本
├── tests/                         # 集成测试
│   └── test_smoke.py              # Smoke 测试（health/ask/cache/熔断）
├── docs/
│   └── api.yaml                   # 共享 API 契约 v1.1.0（唯一真理源）
├── docker-compose.yml             # pgvector 容器
├── .env.example                   # 环境变量模板（含弹性策略配置）
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

### 6. 内测部署方案（推荐）

对于云内测环境，建议使用多 worker 的 Uvicorn 运行方式，并把服务与 pgvector / Ollama / Supabase 作为独立组件部署。

```bash
# 推荐在 Linux 服务器上运行，4核及以上更佳
uvicorn src.api.app:app \
  --host 0.0.0.0 \
  --port 8010 \
  --workers 4 \
  --timeout-keep-alive 10
```

如果你希望更接近生产部署，且已经安装 `gunicorn`：

```bash
gunicorn -k uvicorn.workers.UvicornWorker \
  --workers 4 \
  --threads 4 \
  --bind 0.0.0.0:8010 \
  src.api.app:app
```

#### 内测部署推荐配置

- `AUTH_STUB=false`
- `SUPABASE_URL=https://<your-supabase-project>.supabase.co`
- `SUPABASE_JWT_SECRET=<your-jwt-secret>`
- `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE` 对应你的 PostgreSQL + pgvector 实例
- `OLLAMA_HOST` 或 `OPENAI_API_KEY` / `DEEPSEEK_API_KEY` 根据实际集群情况配置

#### 资源建议

- CPU：4 核以上
- 内存：16GB 以上
- 存储：高速 SSD，避免 pgvector 索引读取延迟
- 网络：如果使用远程 OpenAI/DeepSeek，确保出口带宽稳定

#### 运行建议

- 先启动 `docker compose up -d` 启动 pgvector
- 再启动 Uvicorn 服务
- 最后运行并发容量测试脚本

### 7. 并发容量测试

```bash
python scripts/concurrency_test.py \
  --url http://127.0.0.1:8010/v1/ask \
  --token token-b658c985 \
  --concurrency 5 \
  --requests 20
```

常见测试场景：

- `--concurrency 5 --requests 20`：验证 5 个并发用户是否稳定
- `--concurrency 10 --requests 50`：评估较高并发下的响应时间与失败率

如果你希望阻塞直到服务可用，可以指定 `--ready-url http://127.0.0.1:8010/v1/health`。

### 8. 运行集成 Smoke 测试

```bash
# 确保服务已启动后运行
python tests/test_smoke.py

# 或使用 pytest
python -m pytest tests/test_smoke.py -v -s

# 自定义参数
LOOMA_TEST_URL=http://127.0.0.1:8010 \
LOOMA_TEST_TOKEN=token-b658c985 \
python tests/test_smoke.py
```

## 多 Provider 配置

### LLM Provider

系统按 `LLM_PROVIDER_ORDER` 优先级依次尝试连接 LLM 服务：

```env
# 优先级：ollama > deepseek > openai
LLM_PROVIDER_ORDER=ollama,deepseek,openai

# 为每个 provider 指定 model（可选）
OLLAMA_MODEL=qwen2.5-coder:1.5b
DEEPSEEK_MODEL=deepseek-chat
OPENAI_MODEL=gpt-4o-mini

# API Keys（按需配置）
DEEPSEEK_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx
```

### Embedding Provider

独立于 LLM 的 embedding provider 优先级：

```env
EMBED_PROVIDER_ORDER=ollama,openai,deepseek

OPENAI_EMBED_MODEL=text-embedding-3-small
DEEPSEEK_EMBED_MODEL=deepseek-chat
```

### 查看当前活跃 Provider

```bash
curl http://127.0.0.1:8010/v1/health | jq '{llm_provider, embed_provider}'
```

## 调用弹性策略

系统内置三层容错机制：

| 策略 | 配置 | 说明 |
|------|------|------|
| **调用超时** | `LLM_CALL_TIMEOUT=120` / `EMBED_CALL_TIMEOUT=30` | 单次调用最大等待时间（秒） |
| **自动重试** | `LLM_MAX_RETRIES=2` / `EMBED_MAX_RETRIES=2` | 指数退避重试（0.5s → 1s → 2s） |
| **熔断器** | 5 次连续失败 / 30s 冷却 | 连续失败后短路保护，冷却后半开探测 |

健康检查可查看当前弹性状态：

```bash
curl http://127.0.0.1:8010/v1/health | jq '.resilience'
```

## 两层缓存架构

```
请求 → 请求级缓存 (120s TTL, 64 entries)
     → 意图解析 (LLM) → LLM prompt 级缓存 (300s TTL, 256 entries)
     → 分发执行 → LLM 生成 → LLM prompt 级缓存
     → 响应
```

缓存命中时响应时间 < 50ms（vs 首次 ~80s）。

## 踩坑记录

| 坑 | 修法 |
|----|------|
| 沙箱代理让 ollama-py 卡死 | import 前 pop 6 个代理环境变量 |
| PGVectorStore.delete() 强制要 ref_doc_id | 用 psycopg 直接 TRUNCATE 兜底 |
| PGVectorStore._engine 是 None（懒加载） | 外连 psycopg 做清理 |
| ollama run 退出后模型从显存卸载 | 烟测前预热，或设置 keep_alive 参数 |
| LlamaIndex 0.14 要单独装 ollama embedder | `pip install llama-index-embeddings-ollama` |
| Ollama 冷启动 embeddings API 30s 不响应 | 烟测前 `ollama run` 一次预热，或加 keep_alive |
| CachedLiteLLM 缺少 metadata 导致 LlamaIndex 报错 | 添加 metadata 属性代理到内部 fallback |
| Ollama down 时 embedding 阻断整个 RAG 链路 | Embedding 多 Provider fallback（ollama→openai→deepseek） |

## 下一步（P2 业务功能自然生长）

- 文档导入管道（MarkItDown 解析 → 分块 → embedding → pgvector）
- 跨库检索（本地私有文档 ↔ 远程公共知识）
- 中央大脑意图路由（/v1/ask 自动分发到 rag/resume/jobs）
- Zervi 本地引擎（Rust + sqlx + pgvector + Ollama 本地推理）
- 接 DemoPeter 现有 RAG 面板
