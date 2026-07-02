# MCP 适配底座 — MVP 务实策略

> 状态：已决策  
> 日期：2026-07-02  
> 决策：Python FastMCP Sidecar（MVP 临时适配层）→ Rust zervi 原生 MCP（内测后正式方案）

---

## 1. 两阶段路线

| 阶段 | 方案 | 定位 | 工具数量 |
|------|------|------|---------|
| **MVP 内测（当前）** | `backend/mcp-servers/server.py` (Python FastMCP 2.x) | 临时适配层，快速验证业务闭环 | 3 个 |
| **内测后（未来）** | Rust `zervi/` 原生 MCP | 正式方案，性能 / 类型安全 | 全部 Agent |

### 决策依据

- `feature/llm-provider-fallback-k6-baseline` 分支已引入 Rust `zervi/` 后端内核（`zervi/src/main.rs` 298 行 + `models.rs` 254 行 + `client.rs` 286 行），具备天然 MCP 实现优势
- MVP 阶段不应在 Python MCP 临时层过度投入，保留当前骨架即可
- 待内测验证完成后，由 Rust zervi 一次性接管全部 Agent 并原生暴露为 MCP 工具

---

## 2. MVP 阶段任务（仅 3 项）

### 2.1 🔐 JWT 认证接入 — 必须

**当前状态：** `server.py` 3 个工具完全无认证，任何人可直接调用

**风险：** 内测环境安全底线，必须在上线前修复

**实施方案：**

```python
# backend/mcp-servers/server.py — 在工具函数最前面添加

from src.api.auth.decorators import verify_token_or_raise  # 复用已有装饰器

@mcp.tool(name="rag_query", description="RAG knowledge base query with AI answer")
def rag_query(question: str, user_id: str = "", token: str = "", n_results: int = 3) -> dict:
    # JWT 认证（MVP 最小安全底线）
    if not token:
        raise ValueError("Missing authentication token")
    verify_token_or_raise(token, user_id)
    # ... 原有逻辑 ...
```

**工作量：** ~10 行代码 / 每个工具，总计约 30 行  
**依赖：** `framework-v2` 分支 `b5e9222` 提交已修复 JWT 认证链路（`backend/src/api/auth/decorators.py` + `jwt_handler.py`）

### 2.2 🏥 Health Check — 建议

**当前状态：** MCP Server 无健康检查端点

**目的：** 支撑 CI 脚本（`verify-p0-local.sh` / `verify-closed-loop.sh`）检测 MCP alive

**实施方案：**

```python
# 在 server.py 中添加

@mcp.resource("health://status")
def health_status() -> dict:
    return {
        "status": "ok",
        "service": "looma-mcp-sidecar",
        "tools": ["rag_query", "match_jobs", "parse_resume"],
    }
```

**工作量：** ~10 行代码

### 2.3 📝 工具数量保持 3 个 — 不做扩容

**理由：**
- `rag_query` / `match_jobs` / `parse_resume` 已覆盖内测核心场景
- 后端 18 个 Agent 中其余 15 个（narrative / poetry / mbti / domain_engine 等）推迟到 Rust zervi 阶段
- 避免在 Python 临时层做重复工程

---

## 3. 内测后迁移到 Rust zervi — 衔接约定

为确保前端零改动迁移，Python MCP Sidecar 和 Rust zervi MCP 之间需保持以下接口约定：

| 约定项 | Python 临时方案 | Rust zervi 正式方案 |
|--------|----------------|---------------------|
| 工具命名 | `rag_query` / `match_jobs` / `parse_resume` | 保持同名 |
| 新增工具命名 | — | `narrative_generate` / `poetry_search` / `mbti_analyze` 等 |
| 入参 schema | `question: str, user_id: str, n_results: int` | 保持一致 |
| 出参 schema | `{"answer": str, "sources": [...], ...}` | 保持一致 |
| 传输协议 | SSE (`mcp.run(transport="sse")`) | SSE |
| 端口 | `8999` | `8999` |
| 认证方式 | JWT Token（token 参数） | JWT Token（HTTP Header `Authorization: Bearer`） |
| 内部调用 | 直接 `import src/` | HTTP 调用 `backend/src/api/routes/` |

> ⚠️ Rust zervi 阶段 MCP 不应再通过 `sys.path` 直接 import Python 模块，而是走内部 HTTP API。

---

## 4. Rust zervi 已具备的基础

来自 `origin/feature/llm-provider-fallback-k6-baseline` 分支：

| 文件 | 行数 | 功能 |
|------|------|------|
| `zervi/Cargo.toml` | 21 | Rust 项目配置 |
| `zervi/src/main.rs` | 298 | 服务入口 |
| `zervi/src/models.rs` | 254 | User / 请求响应模型（已有 Tier / UserId 结构） |
| `zervi/src/client.rs` | 286 | HTTP 客户端 |

**缺失部分（待 Sprint）：**
- MCP protocol 适配层（可在内测后作为专项 Sprint）
- 各 Agent 工具的 Rust 实现（目前 Agent 逻辑仍在 Python `backend/src/agents/`）

---

## 5. 当前完成度评分

基于 MVP 临时方案定位重新评估：

| 维度 | 评分 | MVP 是否需要 | 备注 |
|------|------|-------------|------|
| 工具注册 | 🟢 足够 | ✅ | 3 个工具覆盖内测核心场景 |
| JWT 认证 | 🔴 缺失 | ⚠️ **必须补** | 安全底线，约 30 行代码 |
| Health Check | 🔴 缺失 | 🟡 建议补 | 支撑 CI，约 10 行代码 |
| 依赖隔离 | 🟡 可接受 | ❌ | MVP 不强求解耦 |
| 工具扩容 | 🟢 不做 | ❌ | 推迟到 Rust 阶段 |
| 文档 | 🟡 本文档 | ✅ | 已完成 |
| 测试 | 🔴 缺失 | ❌ | 推迟到 Rust 阶段 |
| 可观测性 | 🔴 缺失 | ❌ | 推迟到 Rust 阶段 |

**MVP 适用度：当前 ~60%，补 JWT + Health Check 后可达 ~80%**

---

## 6. 参考分支与提交

| 分支 | 最新提交 | 与 MCP 相关 |
|------|---------|------------|
| `origin/main` | `afb99dd` | — |
| `origin/refactor/framework-v2` | `b5e9222` | 闭环 JWT 认证链路修复、统一 ApiClient |
| `origin/feature/llm-provider-fallback-k6-baseline` | `de2f2c0` | Rust zervi 后端（未来 MCP 方案） |

### MCP 相关提交历史

```
b5e9222 fix: 闭环 JWT 认证链路，统一 ApiClient 与 DB tier 同步    ← JWT 修复
91a930f merge: 接收 szbenyx afb99dd，合并 test_compliance
eb605e1 fix: cherry-pick cn_name redaction from 640cb73
e35240b merge: szbenyx Compliance Gate + Jason Consent UI 与 E2E 适配  ← MCP 恢复
edd9b91 feat: 内测闭环埋点、SaaS 候选者链路与架构审议文档      ← MCP 删除
```

> `edd9b91` 删除了 `mcp-servers/pyproject.toml` 和 `server.py`，`e35240b` 又恢复 — MCP 方案在该分支经历了一次删除→恢复的讨论。

---

## 7. 操作检查清单

### MVP 上线前

- [x] JWT 认证接入 — 3 个 MCP 工具添加 token 验证
- [x] Health Check 端点 — 暴露 `health://status` resource
- [x] `verify-p0-local.sh` 加入 MCP health check 步骤
- [x] Consent 后端 enforce — resume/upload, ask, jobs/match 挂 `@require_consent`
- [x] MCP `parse_resume` 对齐 `resume_upload` consent

### 内测后

- [ ] 开 Rust zervi MCP Sprint（工具实现 + MCP protocol 适配）
- [ ] 18 个 Agent 全部暴露为 MCP 工具
- [ ] 废弃 Python MCP Sidecar，切换到 Rust zervi
- [ ] 前端零改动验证（工具命名/入参/出参保持一致）
- [ ] ADR 归档本文档为最终架构决策
