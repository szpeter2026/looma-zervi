# 协同方案决策回复（szbenyx → Jason）

> **日期：** 2026-07-04（**远端最新** · commit `8286d75` / `f4b9343`）  
> **回复人：** szbenyx（后端 Owner · portal 总负责人 · Enterprise/Jobs/Resume/Reports 路由 Owner）  
> **依据：** `CONSISTENCY_CROSS_REPO_SYNERGY_PROPOSAL.md` v1.0  
> **状态：** 决策文件，请据此排期执行  
> **Jason 确认：** [JASON_DECISION_ACK.md](./JASON_DECISION_ACK.md) · 职责对照 [DUAL_REPO_SYNC_STATUS.md](./DUAL_REPO_SYNC_STATUS.md)

---

## 一、总体评价

方案方向正确，我批准执行。但节奏和分工需调整：**不是「专家研判后立项」，而是即刻开工，我主导、你配合。**

---

## 二、三项决策 — 最终裁定

### 决策 1：契约包拆分 → ✅ 方案 A，落地权在我

`@looma/api-contract` 纯 TS types 包，portal 零 React 依赖。

**我负责：**
- `backend/contracts/` 目录建立，首版含 poetry + auth 两段 OpenAPI
- OpenAPI → TypeScript types 的 codegen 流水线
- 诗词种子数据注入完毕后立即出第一版契约文件

**你需要做的：**
- 不在此包落地前在 planetx/miniprogram 中新增任何镜像类型定义
- shared-core 补导出（题库/合规/常量/IDENTITY_LABELS）— 这是 S0-3，归你

### 决策 2：portal 纳入一致性治理 → ✅ 是，但我划定边界

portal 遵守 G1/G2/G3，**但不等于 portal 参与你的 React monorepo Review**。

| 门禁 | portal 义务 | portal 不参与 |
|------|------------|--------------|
| G1 类型单真源 | 不新增 mirror 类型；消费 `@looma/api-contract` | 不 Review planetx/saas 的 shared-core PR |
| G2 API 行为对齐 | 30s 超时、401 → 跳登录、`looma_token` key | 不参与 UI/组件逻辑统一 |
| G3 文档同步 | 双仓 sync 文档保持一致 | — |

**你需要做的：**
- G1 CI 在 S0 完成前对 portal `poetry.ts` 中的镜像类型仅 warn，不 block
- 契约变更（后端改字段）→ 你提 PR 时必须同时标注 portal 影响

### 决策 3：S0 与 Bolent P0 阻塞关系 → ✅ 软阻塞，以下是我并行推进清单

### 部署策略调整（2026-07-04 更新）

**Jason 的机器性能更强、已有 ChromaDB poetry_full 全量数据（78656 首），因此：**

- **全量诗词注入 + 全栈联调由 Jason 的机器承担**
- **我的 Surface 只做：编码、契约撰写、代码审查、portal 前端开发**

**双仓联调环境：**
```
Jason 高性能机器：
  ├── looma-zervi 全量部署（Flask :5200 + ChromaDB 78656 poems）
  ├── szbolent-portal dev :3000
  └── 带真实数据验证所有 API

我的 Surface：
  ├── 代码编辑（backend/src/、portal/src/）
  ├── 契约文件撰写（contracts/*.json）
  └── portal UI 开发（mock 数据即可）
```

**我即刻并行推进（不依赖你的 S0）：**

| 任务 | 在哪台机器 | 预估 |
|------|-----------|------|
| ~~清理 `backend/mcp-servers/.venv`（292 MB 冗余）~~ | Surface | ✅ 已完成 |
| ~~`requirements.txt` 补齐 fastmcp + chromadb~~ | Surface | ✅ 已完成 |
| `backend/contracts/poetry.v1.json` 首版 | Surface 撰写 → Jason 机器验证 | 0.5d |
| portal P0-P4：清 `:8001` legacy proxy | Surface | 10min |
| portal P0-P1：生产 `VITE_LOOMA_API_BASE` 注入 | Surface | 10min |
| portal P0-P7：隐私/协议静态页 | Surface | 0.5d |
| portal `looma.ts` fetch 薄封装（泛型） | Surface | 0.5d |
| portal Pricing 页面 UI 骨架（mock 数据） | Surface | 1d |

**你需要并行推进：**

| 任务 | 预估 |
|------|------|
| S0-3：shared-core 补导出（题库、personality、IDENTITY_LABELS、getRankName） | 1d |
| **诗词种子注入 + ChromaDB 向量重建**（在你的高性能机上） | 0.5d |
| **双仓同时部署联调**（looma :5200 + portal :3000，带全量诗词验证） | 持续 |
| 报告 Sprint 1 #2：题库 → shared-core | 看你的排期 |
| 报告 Sprint 1 #1：小程序 npm 接入 shared-core | 看你的排期 |

**等 S0 契约文件就绪后我再做的：**
- portal `looma.ts` 完整类型定义（auth/payment/compliance）
- portal Pricing 页接真实 API

> **⚠️ 文档内部待对齐：** §四 #1 与 §六 仍写「诗词注入归我」；以 **§部署策略调整** 为准 → **注入 + 联调归 Jason**。见 `DUAL_REPO_SYNC_STATUS.md`。

---

## 三、你的行动清单（按优先级）

| # | 任务 | 截止 | 产出 |
|---|------|------|------|
| 1 | **S0-3** shared-core 补导出：题库/合规/常量 | W1 末 | PR to `packages/shared-core` |
| 2 | **报告 Sprint 1 #2** 题库 → shared-core 迁移 | W2 中 | planetx/saas 不再本地维护题库 |
| 3 | **报告 Sprint 1 #1** 小程序 npm 接入 shared-core | W2 末 | miniprogram 不再手工复制类型 |
| 4 | **报告 Sprint 1 #3** 合规碎片统一 | W3 中 | ConsentScope 全端单真源 |
| 5 | 确认 CORS 生产配置 `CORS_ORIGINS` 含 `szbolent.cn` | W1 中 | 我这边 portal 联调 CORS |
| 6 | `verify-closed-loop.sh` 扩展（poetry random/browse/stats） | W1 末 | 脚本就绪 |
| 7 | `/v1/poetry/authors` 分页接口 RFC | W2 中 | portal 不再客户端聚合诗人 |

---

## 四、我的并行行动清单

| # | 任务 | 截止 | 产出 |
|---|------|------|------|
| 1 | ~~looma.db 注入 78656 首诗词种子数据~~ → **已转 Jason 机器** | — | 见部署策略 |
| 2 | `backend/contracts/poetry.v1.json` 导出 | W1 中 | 契约真源 v0.1 |
| 3 | `backend/contracts/auth.v1.json` 导出 | W1 末 | 契约真源 v0.1 |
| 4 | portal：删 `:8001` proxy + `tatha.ts` + `business.ts` | W1 初 | legacy 清零 |
| 5 | portal：`looma.ts` fetch 封装 + 静态页 | W1 中 | P0-P2/P0-P7 |
| 6 | portal：Pricing UI 骨架 | W1 末 | P0-P3 |
| 7 | ~~清理 `mcp-servers/.venv`~~ | — | ✅ 已完成 |

---

## 五、协同节奏（我定的）

| 频次 | 形式 | 主持 |
|------|------|------|
| **每周一** | 15min sync：契约变更、blocker、进度对齐 | 我 |
| **PR 提审** | shared-core / contracts 变更 → 我 Review | 我 |
| **文档 sync** | `DUAL_REPO_WORK_GUIDE.md` 改动 → 你同步到我仓 | 你 |

---

## 六、关于种子数据 — 你需要知道的事实

- **28 张表 schema 完备**；**poems 表基本为空**（需 `import_poetry.py`）
- **ChromaDB `data/poetry_full` 全量在 Jason 机器**（78656 首）
- **注入与联调在 Jason 高性能机执行**（2026-07-04 部署策略）

---

## 七、确认事项

请在 **2026-07-05 前**确认以下三项：

- [x] 接受上述分工和截止时间 — Jason 2026-07-04
- [x] 确认 S0-3 可在 W1 末完成 — 已启动
- [x] 确认 CORS 可在诗词注入后就绪 — `.env.example` 已更新

---

**szbenyx** · 2026-07-04
