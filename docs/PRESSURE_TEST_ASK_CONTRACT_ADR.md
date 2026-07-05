# 压测焦虑纠偏与 Ask 契约统一 — 架构决策记录（ADR）

> **版本：** 1.0 · **日期：** 2026-07-06  
> **状态：** P0 已完成 · P1 内测并行  
> **关联分支：** `github/feature/llm-provider-fallback-k6-baseline`  
> **关联文档：** [LOCAL_MVP_DEBUGGING.md](./LOCAL_MVP_DEBUGGING.md) · [MINIPROGRAM_LOCAL_DEBUGGING.md](./MINIPROGRAM_LOCAL_DEBUGGING.md) · [CONSISTENCY_CROSS_REPO_SYNERGY_PROPOSAL.md](./CONSISTENCY_CROSS_REPO_SYNERGY_PROPOSAL.md)  
> **目的：** 记录团队对内测前「客户端 / SaaS 压测」焦虑的理解偏差、核实结论与后续合入 main 的工作清单

---

## 1. 背景：焦虑从哪来

内测前团队担心：

- C 端（PlanetX）、B 端（SaaS）、小程序在并发下是否扛得住；
- `@looma/shared-core` 多端契约是否足够，是否还要 Rust 重构；
- 远端 **LLM 分支**（`feature/llm-provider-fallback-k6-baseline`）曾做过 k6 基线，与当前 **main** 是否脱节；
- Multica 式「分层 + 契约 + 依赖向下」是否只解决了 80%，剩下 20% 会不会在内测爆雷。

---

## 2. 原理解（焦虑点）→ 纠偏对照表

| # | 原理解 / 焦虑点 | 纠偏结论 | 证据 |
|---|----------------|----------|------|
| A1 | **shared-core 不够，内测会在多端一致性上崩** | ✅ 契约层已基本就绪（路径、consent、工厂、小程序 bundle）；内测主要风险**不在**类型漂移 | P1 四条链路已切 shared-core；Playwright API 种子在 main 上 register/profile-sync/referral 正常 |
| A2 | **需要尽快 Rust 重构 shared-core 才能扛压** | ❌ 压测瓶颈不在 TS 契约层；Rust 重构是 **MVP 后 Phase R**，内测前不应阻塞 | `zervi-rust` 是 ADIRP 微服务后端，非 shared-core 替代品；无 WASM/npm 客户端 |
| A3 | **客户端 + SaaS 要做浏览器 100 并发压测** | ❌ 应 **API 层 k6 压 `/v1/ask`** + 少量（5–10）人工/SaaS 冒烟；浏览器压测混合 UI/SSE/CORS，结论不清晰 | LLM 分支仅有 `k6_ask_test.js`、`concurrency_test.py`，无 Web UI 压测 |
| A4 | **LLM 分支的压测结论可直接用于 main** | ⚠️ **方向可用，参数不可直接套用**：端口、目录结构、LLM 栈均已变化 | 分支 `:8010` + `src/core/llm.py`；main `:5200` + `backend/src/agents/central_brain.py` |
| A5 | **小程序和 Web 在 Ask 上压力相同** | ❌ 小程序走 **非流式 POST**（与当前后端一致）；SaaS 走 **假 SSE 读流**（与后端不一致），SaaS 风险更高 | 见 §4 |
| A6 | **Multica 80% = 还缺 20% 架构没做** | ✅ 缺的 20% 是 **容量 / LLM resilience / Ask 传输契约**，不是再拆 `@looma/core` 包 | shared-core RULE：仅契约，不含 UI/Store |
| A7 | **ChromaDB Docker :8000 是 MVP 必需** | ❌ 诗词 RAG 用 `data/poetry_full` 本地 PersistentClient；Docker Chroma 为可选扩展 | `backend/dev.sh` · `rehearsal-local.sh` |
| A8 | **PlanetX 本地联调默认连本地后端** | ✅ fallback 已改为 `http://127.0.0.1:5200`；生产/build 仍须设 `VITE_API_BASE` | `planetxAuthStore.ts` · MVP 启动脚本 |

---

## 3. 核实发现（2026-07-06）

### 3.1 shared-core 边界（Multica 对照）

```
┌─────────────────────────────────────────────────────────┐
│  views：planetx / saas / miniprogram pages              │
├─────────────────────────────────────────────────────────┤
│  UI 栈：brand/ui (Web) · wx 组件 (小程序)  — 平台独立    │
├─────────────────────────────────────────────────────────┤
│  契约层：@looma/shared-core（API_ROUTES / 工厂 / 类型）  │  ← 已完成 ~80%
├─────────────────────────────────────────────────────────┤
│  传输层：ApiClient(fetch) · MiniApiClient(wx.request)    │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────┐
│  Flask :5200 — quota / consent / RAG / LLM               │  ← 压测与 resilience 焦点
└─────────────────────────────────────────────────────────┘
```

**结论：** shared-core 解决「说同一种话」；**不解决** worker 数、LLM 延迟、并发排队。

### 3.2 LLM 分支已有资产（`feature/llm-provider-fallback-k6-baseline`）

| 资产 | 路径（分支内） | 作用 |
|------|----------------|------|
| k6 Ask 基线 | `scripts/k6_ask_test.js` | VU=1–2，p95 首请求 ~44s（缓存 miss） |
| k6 无缓存对比 | `scripts/k6_ask_test_nocache.js` | 每请求唯一 query |
| 并发脚本 | `scripts/concurrency_test.py` | 多线程 `/v1/ask` |
| LLM fallback | `src/core/llm.py` | LiteLLM + provider 顺序 + 熔断 |
| LLM 缓存 | `src/core/llm_cache.py` | TTL + LRU（256 条 / 300s） |
| 基线报告 | `k6_comparison_report.json` | Ollama ~37s avg → DeepSeek ~3s avg（VU=1） |
| API 契约 | `docs/api.yaml` v1.1.0 | 分支真源（main 尚未完全对齐） |
| Rust CLI | `zervi/src/client.rs` | 打 API，非 Web 压测 |

**分支结论（2026-06-17）：** DeepSeek 端到端 ~3s 可接受；**未测** main 架构下多 VU nocache、SaaS 长连接、gunicorn 多 worker。

### 3.3 main 当前状态（MVP 内测真源）

| 项 | main 现状 | 与 LLM 分支差距 |
|----|-----------|----------------|
| 端口 | `:5200` | 分支 `:8010` |
| Ask 缓存 | `ask_routes.py` 结果缓存 64 条 / 120s | 分支另有 LLM 层缓存 |
| LLM 调用 | `central_brain.py` 简单 provider 顺序 | 无 LiteLLM / 熔断 / 可观测性 |
| k6 / concurrency 脚本 | ❌ 未合入 | 分支有 |
| 部署进程 | `dev.sh` 单进程 Flask | 内测并发需 gunicorn |
| Playwright E2E | ✅ `e2e:live:all`（SaaS + PlanetX） | 测 UI 闭环，非 Ask 容量 |

### 3.4 Ask 契约不一致（P0 缺陷）

| 端 | 客户端实现 | 期望 | 后端 `ask_routes.py` | 一致？ |
|----|-----------|------|----------------------|--------|
| **小程序** | `createChatApi().ask()` | JSON 一次返回 | `jsonify(...)` | ✅ |
| **SaaS** | `useChat.ts` → `fetch` + `body.getReader()` | SSE 流式 | `jsonify(...)` | ❌ |
| **shared-core Web** | `createChatApi().askStream()` | SSE | 未实现 stream 路由 | ❌ |

**影响：**

- SaaS 多用户同时提问 → 多个**长连接阻塞**至 LLM 完成（数秒～数十秒）；
- Flask 单 worker 下第二个 Ask 会排队；
- UI 表现为「一直空白直到突然出字」，内测易被误判为前端 bug。

**纠偏：** 内测前优先 **统一为非流式 JSON**（改 SaaS 用 shared-core `ask()`），或 **后端真 SSE**（工作量大，放 P1）。

---

## 4. 压力测试分层（正确做法）

| 层级 | 测什么 | 工具 | 负责人 |
|------|--------|------|--------|
| L1 API 容量 | `POST /v1/ask` nocache/cache、429 quota | k6 + `concurrency_test.py`（从分支移植） | 后端 |
| L2 合规/闭环 | consent、credit、referral | `verify-p0-local.sh` · Playwright live | 全栈 |
| L3 SaaS 冒烟 | 5–10 并发 HR 提问（手工或轻脚本） | 内测志愿者 | 产品 |
| L4 Web UI 压测 | ❌ 内测不做 100 浏览器并发 | — | — |
| L5 小程序 | 真机四条链路 | 微信开发者工具 | 前端 |

**内测 SLO 建议（待跑 k6 后确认）：**

| 指标 | 目标 | 备注 |
|------|------|------|
| Ask p95（DeepSeek，nocache，VU≤5） | < 8s | 分支 VU=1 约 3s avg |
| Ask p95（cache hit） | < 500ms | 相同 query 120s 内 |
| 错误率 | < 5% | 不含预期 429 |
| 429 quota | 按 tier 设计 | guest/free 耗尽为正常 |

---

## 5. 后续工作清单（LLM 分支 → main）

### Phase P0 — 内测前（软阻塞 SaaS Ask）

- [x] **P0-1** 从分支移植 `scripts/k6_ask_test.js`、`scripts/k6_ask_test_nocache.js`、`scripts/concurrency_test.py`，`LOOMA_URL=http://127.0.0.1:5200`
- [x] **P0-2** 跑 nocache 基线（VU=1,5）并记录到 `docs/k6_baseline_main.json`
- [x] **P0-3** **统一 Ask 契约（推荐路径 A）**：SaaS `useChat` 改为 `createChatApi(client).ask()` 非流式；或路径 B 后端实现 SSE
- [x] **P0-4** 内测部署用 **gunicorn ≥4 workers**（文档写入 `LOCAL_MVP_DEBUGGING.md`）
- [x] **P0-5** MVP 脚本 export `VITE_API_BASE=http://127.0.0.1:5200`（PlanetX 勿打 staging）
- [x] **P0-6** shared-core 增加 `PLATFORM_CAPS.askStream` 文档化（Web/SaaS/Mini 能力矩阵）

### Phase P1 — 内测并行

- [ ] **P1-1** Cherry-pick 或移植 LLM 分支：`llm_cache` 思路 + provider fallback + 熔断（适配 `central_brain.py`，非整仓合并）
- [ ] **P1-2** k6 nocache 5 VU × 20 req；对比 main 与分支报告
- [ ] **P1-3** CI 可选 job：`k6` smoke（VU=1，需 `DEEPSEEK_API_KEY` secret）
- [ ] **P1-4** 合入/对齐 `docs/api.yaml` 中 `/v1/ask` 请求/响应 schema（含 stream 布尔或分路由）

### Phase P2 — 内测后

- [ ] **P2-1** 若 p95 仍超标：Ask 异步队列（Redis/Celery）
- [ ] **P2-2** 真 SSE + `createChatApi().askStream()` 与后端对齐
- [ ] **P2-3** Rust `looma-contracts` / zervi CLI 复用 k6 场景（MVP 后）

---

## 6. 明确不做（避免焦虑驱动的过度工程）

| 不做 | 原因 |
|------|------|
| MVP 前 Rust 重写 shared-core | 不解决 LLM 并发 |
| MVP 前新建 `@looma/core` / `shared-types` 包 | 与 shared-core 重复 |
| 浏览器 100 并发压 PlanetX/SaaS | 结论混叠，应用 k6 打 API |
| 整分支 merge `feature/llm-provider-fallback-k6-baseline` | 目录结构不同（`src/` vs `backend/`），冲突大 |
| 内测强依赖 ChromaDB Docker :8000 | 非诗词 RAG 主路径 |

---

## 7. 关键代码索引（main）

| 主题 | 路径 |
|------|------|
| Ask 路由 + 结果缓存 | `backend/src/api/routes/ask_routes.py` |
| LLM 调用 | `backend/src/agents/central_brain.py` |
| Quota | `backend/src/utils/quota.py` |
| SaaS 假 SSE | `frontend/packages/saas/src/features/chat/useChat.ts` |
| shared-core Ask 工厂 | `frontend/packages/shared-core/src/api/createApi.ts` |
| 小程序 Ask | `frontend/packages/miniprogram/pages/ask/index.ts` |
| API 路径常量 | `frontend/packages/shared-core/src/constants/routes.ts` |
| Playwright 闭环 | `frontend/e2e/closed-loop.live.spec.ts` |

## 8. 关键代码索引（LLM 分支）

```bash
git show github/feature/llm-provider-fallback-k6-baseline:scripts/k6_ask_test.js
git show github/feature/llm-provider-fallback-k6-baseline:scripts/concurrency_test.py
git show github/feature/llm-provider-fallback-k6-baseline:src/core/llm.py
git show github/feature/llm-provider-fallback-k6-baseline:k6_comparison_report.json
```

---

## 9. 一句话摘要

> **焦虑的真实对象是 LLM 链路的容量与 Ask 传输契约，不是 shared-core 多端统一。**  
> LLM 分支已在 API 层证明 DeepSeek ~3s 可行，但 main 未合入压测脚本与 resilience；SaaS 假 SSE 会在内测放大并发问题。  
> **下一步：移植 k6 → 统一 Ask 为非流式或真 SSE → cherry-pick LLM fallback → 定 SLO。**

---

*维护：内测前由 Jason 确认 P0 勾选；k6 基线跑完后更新 §4 SLO 表格。*
