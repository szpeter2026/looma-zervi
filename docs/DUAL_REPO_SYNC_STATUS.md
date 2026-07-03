# 双仓远端同步状态与职责对照

> **更新：** 2026-07-04 · 对照 szbenyx 远端推送  
> **远端：** [looma-zervi `8286d75`](https://github.com/szpeter2026/looma-zervi) · [szbolent-portal `f4b9343`](https://github.com/szpeter2026/szbolent-portal)

---

## 1. 远端推送摘要

| 仓 | Commit | 作者 | 内容 |
|----|--------|------|------|
| **looma-zervi** | `8286d75` | szbenyx | `docs/DECISION_RESPONSE.md`（含**部署策略调整**）；`requirements.txt` +fastmcp、chromadb 版本放宽 |
| **szbolent-portal** | `f4b9343` | szbenyx | 同步同上 `DECISION_RESPONSE.md` |

**szbenyx 已在 Surface 完成：** 清理 `mcp-servers/.venv` · `requirements.txt` 补齐

**尚未在远端看到（仍待 szbenyx Surface 推送）：** portal 清 legacy、`looma.ts`、contracts、Pricing UI

---

## 2. 本地 vs 远端同步状态

### looma-zervi

| 项 | 本地分支 | 远端 `github/main` | 说明 |
|----|----------|-------------------|------|
| 当前分支 | `refactor/framework-v2` @ `a47262e` | `8286d75` | 本地 **落后 main 1 commit**（szbenyx 文档+requirements） |
| Jason 未推送工作 | 大量 modified/untracked | 无 | S0-3、CORS、verify 脚本、docs 等 **仅在本机** |

**建议操作：**
```bash
cd looma-zervi
git merge github/main          # 或 cherry-pick 8286d75
# 再 commit + push Jason 侧改动至 github
```

### szbolent-portal

| 项 | 本地 | 远端 `origin/main` | 说明 |
|----|------|-------------------|------|
| HEAD | `4072713` | `f4b9343` | **落后 1 commit**（DECISION_RESPONSE） |
| portal 代码 | legacy `:8001` 仍在 | 同左 | szbenyx P0 任务 **尚未推送** |

**建议操作：**
```bash
cd szbolent-portal
git pull origin main           # 合并 f4b9343
```

---

## 3. 职责矩阵（以最新「部署策略」为准）

### szbenyx — Surface 机器

| 领域 | 职责 | 状态 |
|------|------|------|
| **契约** | `backend/contracts/*.json` 撰写、codegen 设计 | 待做 |
| **Portal 前端** | 清 legacy、looma.ts 薄封装、legal 页、Pricing UI mock | 待推送 |
| **Review** | shared-core / contracts PR | 持续 |
| **主持** | 周一 15min sync | — |
| **后端路由** | Enterprise/Jobs/Resume/Reports Owner | 不变 |
| ~~诗词注入~~ | ~~W1 #1~~ | **已转 Jason** |

### Jason — 高性能机器（本机 `/Users/jason/Projects`）

| 领域 | 职责 | 本地进度 |
|------|------|----------|
| **联调真源** | Flask :5200 + 全量 `poetry_full` + portal :3000 | 待跑 import + 常驻联调 |
| **诗词注入** | `import_poetry.py` → looma.db | **待做（新归你）** |
| **shared-core** | S0-3 题库/人格/IDENTITY_LABELS | ✅ 已编码，待 push |
| **planetx** | 报告 #2 迁移 import shared-core | ✅ 已做 |
| **miniprogram** | 报告 #1 npm 接入 | W2 待做 |
| **合规** | 报告 #3 miniprogram consent | W3 待做 |
| **CORS** | 生产 `.env` 含 szbolent.cn | ✅ example+config 已改 |
| **烟雾测试** | verify-closed-loop + poetry | ✅ 已扩展 |
| **RFC** | `/v1/poetry/authors` | ✅ 已写，待 szbenyx review |
| **文档 sync** | 双仓 sync 文档到 portal 远端 | 进行中 |
| **planetx/miniprogram** | 不新增镜像类型；后端 PR 标注 portal 影响 | 遵守中 |

### 双方边界

| Jason **不做** | szbenyx **不做** |
|----------------|------------------|
| portal UI / Pricing 页面实现 | 全量诗词 import（在 Jason 机） |
| `@looma/api-contract` codegen 落地 | planetx/saas shared-core 日常开发 |
| Review 自己的 shared-core（szbenyx Review） | Jason 机器上的 deploy 运维（Jason 负责） |

---

## 4. Jason 行动清单（更新后优先级）

| 优先级 | 任务 | 说明 |
|--------|------|------|
| **P0** | `git merge` 远端 + push 本地 S0-3/CORS/docs | 与 szbenyx 对齐 |
| **P0** | 运行 `import_poetry.py` 灌入 78656 首 | 联调前置；原 szbenyx W1#1 |
| **P0** | 本机双仓联调：`:5200` + portal `:3000` | 给 contracts 验证用 |
| **P1** | push 后请 szbenyx Review shared-core PR | |
| **P1** | 生产机 `CORS_ORIGINS` 写入真实 `.env` | 非 example |
| **P2** | miniprogram npm + consent（W2–W3） | |
| **P2** | 实现 `/v1/poetry/authors`（RFC 通过后） | 与 szbenyx 协商 Owner |

---

## 5. 文档真源位置

| 文档 | 真源 |
|------|------|
| `DECISION_RESPONSE.md` | 远端 szbenyx 版 + 本地 amendment（§四/§六） |
| `JASON_DECISION_ACK.md` | Jason 确认 |
| `DUAL_REPO_WORK_GUIDE.md` | 双仓 sync（Jason 改 → push portal） |
| `DUAL_REPO_SYNC_STATUS.md` | 本文（同步状态，有冲突时以部署策略为准） |

---

## 6. 待周一 sync 确认的一点

§四 #1 与「部署策略」文字冲突：以 **诗词注入归 Jason** 为准；建议 szbenyx 下版 DECISION 删改 §四#1 与 §六末句，避免歧义。
