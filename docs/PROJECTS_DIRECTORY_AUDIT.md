# Projects 目录勘查记录与处置建议

> **版本：** 1.0 · **勘查日期：** 2026-07-03  
> **状态：** 仅文档记录，**未执行任何删除或迁移**  
> **同步副本：**  
> - `looma-zervi/docs/PROJECTS_DIRECTORY_AUDIT.md`  
> - `szbolent-portal/docs/PROJECTS_DIRECTORY_AUDIT.md`  
> **关联：** [DUAL_REPO_WORK_GUIDE.md](./DUAL_REPO_WORK_GUIDE.md) · portal 专用：`LINEAGE.md`、`INTEGRATION.md`（同目录）

---

## 1. 勘查目的

在构建 **looma-zervi × szbolent-portal** 双仓体系后，对 `/Users/jason/Projects` 目录及关联 SurfaceZervi 登记项进行对照审查，区分：

- 双仓日常交付所需  
- 战略相关但非日常改代码  
- 已被取代的 legacy 副本  
- 明确无关项  

**本次结论：** 占用资源有限（潜在可清理约 **~300MB**），**暂不删除**；本文档供后续迭代或磁盘整理时参照。

---

## 2. 勘查范围

| 范围 | 路径 | 是否纳入 |
|------|------|----------|
| 工程根目录 | `/Users/jason/Projects` | ✅ |
| 双仓核心 | `looma-zervi/`、`szbolent-portal/` | ✅ |
| 博物馆登记 | `/Users/jason/SurfaceZervi`（MANIFEST、snapshots、archive） | ✅ 顺带 |
| 其他磁盘路径 | `~/PlanetX`（若与 Projects/PlanetX 重复） | ❌ 未深查 |

---

## 3. 核心保留（双仓体系 · 勿删）

### 3.1 工程目录

| 路径 | 角色 |
|------|------|
| `looma-zervi/` | API 真源、PlanetX/T-space 前端、微信小程序、诗词/RAG/支付 |
| `szbolent-portal/` | `szbolent.cn` 门户壳（Vue SPA） |

### 3.2 双仓文档（均相关）

**looma-zervi/docs/**

| 文档 | 用途 |
|------|------|
| `DUAL_REPO_WORK_GUIDE.md` | 双仓协作工作指引 |
| `TENCENT_CLOUD_COMMERCE.md` | 备案 / 支付 / P0–P2 |
| `COMMERCE_ENTITY_DECISION.md` | 主体与费用选型 |
| `MCP底座交付说明_内测.md` | MCP Sidecar 内测（与 Flask `:5200` 并行） |
| `PROJECTS_DIRECTORY_AUDIT.md` | 本文档 |

**szbolent-portal/docs/**

| 文档 | 用途 |
|------|------|
| 上述同步文档（4 份） | 与 looma 同文 |
| `INTEGRATION.md` | WP / Looma 联调 |
| `LINEAGE.md` | 溯源与边界 |
| `SOURCE.json` | MANIFEST 机器登记 |

### 3.3 运行时数据

| 路径 | 大小（勘查时） | 说明 |
|------|----------------|------|
| `looma-zervi/data/poetry_full/` | ~300MB | 诗词 ChromaDB；后端 `POETRY_CHROMA_PATH` 硬依赖 |

---

## 4. 相关但非双仓日常交付（建议保留）

| 路径 | 大小（勘查时） | 与双仓关系 | 建议 |
|------|----------------|------------|------|
| `PlanetX/` | ~4.9GB | JobFirst 主工作区；MANIFEST `engineering_workspace` | **保留**；与 Bolent 叙事分离 |
| `SurfaceZervi/` | — | 博物馆 + MANIFEST → `szbolent-portal` | **保留**；非日常改代码入口 |
| `SurfaceZervi/archive-gitee/szbenyx/bolent/web-public` | — | szbolent-portal 继承基线 | **保留**（溯源） |
| `SurfaceZervi/snapshots/chinese-poetry-corpus-*` | — | 诗词语料快照 | **保留**（数据备份） |
| `SurfaceZervi/GitHub/xiajason/szbolent-frontend` | — | 旧 Vue 品牌壳；LINEAGE 注明勿与 portal 混淆 | **保留**（登记副本） |

---

## 5. 处置建议（暂未执行）

### 5.1 明确无关 — 未来可删

| 路径 | 大小 | 理由 |
|------|------|------|
| `test_write` | 0B | 空文件，测试残留 |
| `300662科锐国际/` | ~32MB | 科锐国际财报 docx，无代码引用 |
| `数据分析与python实战-代码/` | ~30MB | Python 教程 notebook，无项目引用 |

**潜在释放：~62MB**

---

### 5.2 已被双仓体系取代 — 未来可删或移出 Projects

| 路径 | 大小 | 理由 | 删除前需确认 |
|------|------|------|--------------|
| `planex-miniprogram/` | ~484KB | 旧 JS 小程序；真源：`looma-zervi/frontend/packages/miniprogram`（TS，功能更全） | 微信开发者工具不再打开此目录 |
| `tatha-frontend/` | ~236KB | 静态 HTML 预览；Tatha RAG 已融入 Looma `backend/src/rag/` | GitHub / MANIFEST 仍有登记副本 |
| `Tatha+DemoPeter_融合决策_底座优先修订版.md` | ~18KB | 历史决策；结论已体现在 looma 架构 | 可先归档至 SurfaceZervi/docs |
| `Tatha与DemoPeter_分析融合决策文档.md` | ~32KB | 同上 | 同上 |

**说明：** `planex-miniprogram` 配置仍指向 `api.genz.ltd` + Supabase，与当前 `api.szbolent.cn` / Looma `:5200` 路线不一致，属过期副本。

**潜在释放：~800KB + 文档**

---

### 5.3 数据压缩包 — 未来可删（已有解压 / 快照）

| 路径 | 大小 | 理由 |
|------|------|------|
| `poetry_full.rar` | ~177MB | 已解压至 `looma-zervi/data/poetry_full/` |
| `中华诗词汇总源数据.rar` | ~61MB | 导入源；SurfaceZervi 有 `chinese-poetry-corpus` 快照 |

**删除前需确认：** 外部备份或 SurfaceZervi snapshots 仍可恢复。

**潜在释放：~238MB**

---

### 5.4 构建产物 — 未来可删本地（可重建）

| 路径 | 大小 | 理由 |
|------|------|------|
| `szbolent-portal/dist/` | ~488KB | 已在 `.gitignore`；`npm run build` 可重建 |

---

### 5.5 建议迁移而非删除

| 路径 | 问题 | 建议 |
|------|------|------|
| `Projects/api.yaml` | `looma-zervi/package.json` 描述引用 `docs/api.yaml`，文件却在 Projects 根 | 移入 `looma-zervi/docs/api.yaml` 作契约真源（见 DUAL_REPO_WORK_GUIDE §8） |
| 融合决策 2 份 `.md` | 有历史价值 | 移入 `SurfaceZervi/docs/archive/` 后从 Projects 根移除 |

---

## 6. 双仓内部待清理项（代码层 · 非本次磁盘勘查）

以下在 `DUAL_REPO_WORK_GUIDE.md` P0 中已跟踪，与 Projects 根目录删留无关：

| 项 | 位置 | 处置方向 |
|----|------|----------|
| Legacy `:8001` | `szbolent-portal/vite.config.ts`、`activity.ts`、`business.ts` | 迁移至 Looma 或下线 |
| 废弃 Tatha 客户端 | `szbolent-portal/src/api/tatha.ts` | 生产禁用；确认无引用后删除 |
| 门户未 init git | `szbolent-portal/` | 建议初始化版本控制 |

---

## 7. 关系总览

```text
【双仓日常交付 · 保留】
  looma-zervi ──HTTP /v1/*──► szbolent-portal

【战略相关 · 保留】
  PlanetX/              JobFirst 主线（与 Bolent 分离）
  SurfaceZervi/         MANIFEST + 语料快照 + web-public 基线

【过期副本 · 暂留，未来可删】
  planex-miniprogram/   ← looma miniprogram 已取代
  tatha-frontend/       ← Looma rag 已取代
  Projects/*.rar        ← 已解压 / 有 snapshot

【无关 · 暂留，未来可删】
  300662科锐国际/
  数据分析与python实战-代码/
  test_write
```

---

## 8. 审定清单（供日后执行时勾选）

勘查时建议、**均未执行**。日后若需清理，可按编号确认：

| # | 路径 | 建议 | 潜在释放 |
|---|------|------|----------|
| 1 | `test_write` | 删 | 0 |
| 2 | `300662科锐国际/` | 删 | ~32MB |
| 3 | `数据分析与python实战-代码/` | 删 | ~30MB |
| 4 | `planex-miniprogram/` | 删 | ~484KB |
| 5 | `tatha-frontend/` | 删 | ~236KB |
| 6 | `Tatha+DemoPeter_融合决策_底座优先修订版.md` | 删或归档 | ~18KB |
| 7 | `Tatha与DemoPeter_分析融合决策文档.md` | 删或归档 | ~32KB |
| 8 | `poetry_full.rar` | 删 | ~177MB |
| 9 | `中华诗词汇总源数据.rar` | 删 | ~61MB |
| 10 | `szbolent-portal/dist/` | 删（可重建） | ~488KB |
| 11 | `api.yaml` | 迁移至 `looma-zervi/docs/` | — |

**若 1–10 全部执行：约 ~300MB。**  
**2026-07-03 审定结论：暂不删除，仅本文档记录。**

---

## 9. 明确不建议删除

- `looma-zervi/`、`szbolent-portal/` 及其中全部 docs  
- `PlanetX/`  
- `SurfaceZervi/`（含 snapshots、archive、MANIFEST）  
- `looma-zervi/data/poetry_full/`

---

## 10. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-07-03 | 初版勘查；决定暂留所有项，仅文档记录 |
