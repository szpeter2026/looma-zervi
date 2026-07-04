# 双仓远端同步状态与职责对照

> **更新：** 2026-07-04 · 第一轮联调后  
> **联调报告：** [ROUND1_INTEGRATION_REPORT.md](./ROUND1_INTEGRATION_REPORT.md) ← **szbenyx 请阅并认领 §6.2**  
> **远端：** [looma-zervi `27762f5`](https://github.com/szpeter2026/looma-zervi) · [szbolent-portal `2f7a202`](https://github.com/szpeter2026/szbolent-portal)

---

## 0. 第一轮联调结论（2026-07-04）

| 链路 | 状态 | 说明 |
|------|------|------|
| looma `:5200` + portal诗词 | ✅ 通过 | browse/random/stats/authors、verify 脚本全绿 |
| portal `:3000` + WP `:8800` | ⚠️ 部分 | REST 通；内容仅 1 篇、ErphpDown 未配 |
| 三服务联调文档 | 📝 已写 | 见 `ROUND1_INTEGRATION_REPORT.md` |

**Jason 本地未 push：** looma S0-3 merge、portal About/compose 改动、本报告。

---

## 1. 远端推送摘要

| 仓 | Commit | 作者 | 内容 |
|----|--------|------|------|
| **looma-zervi** | `27762f5` | szbenyx | CORS `:3000`、`/v1/poetry/authors`、verify P0-L4 |
| **szbolent-portal** | `2f7a202` | szbenyx | P0-P5/P0-P6 legacy 归档 |

**szbenyx 已在 Surface 完成：** legacy 归档 · authors API · verify 扩展

**仍待 szbenyx：** `looma.ts`、contracts、Pricing UI、vite 清 `:8001`、compose WP 默认值合并（见 ROUND1 §6.2）

---

## 2. 本地 vs 远端同步状态

### looma-zervi

| 项 | 本地分支 | 远端 `github/main` | 说明 |
|----|----------|-------------------|------|
| 当前分支 | `refactor/framework-v2` @ `fb31eaf` | `27762f5` | 已 merge szbenyx；Jason 改动 **待 push** |
| Jason 未推送工作 | ROUND1 报告、S0-3 等 | 无 | 见 `ROUND1_INTEGRATION_REPORT.md` §6.1 |

**建议操作：**
```bash
cd looma-zervi
git push github refactor/framework-v2
```

### szbolent-portal

| 项 | 本地 | 远端 `origin/main` | 说明 |
|----|------|-------------------|------|
| HEAD | 本地含联调文档 | `2f7a202`+ | legacy 归档已在远端；联调报告 **待 push** |

**建议操作：**
```bash
cd szbolent-portal
git push origin main
```

---

## 3. 职责矩阵（以最新「部署策略」为准）

### szbenyx — Surface 机器

| 领域 | 职责 | 状态 |
|------|------|------|
| **契约** | `backend/contracts/*.json` 撰写、codegen 设计 | 待做 |
| **Portal 前端** | 清 legacy、looma.ts 薄封装、legal 页、Pricing UI mock | 部分完成 |
| **Review** | shared-core / contracts PR | 持续 |
| **主持** | 周一 15min sync | — |
| **后端路由** | Enterprise/Jobs/Resume/Reports Owner | 不变 |
| ~~诗词注入~~ | ~~W1 #1~~ | **已转 Jason** |

### Jason — 高性能机器（本机 `/Users/jason/Projects`）

| 领域 | 职责 | 本地进度 |
|------|------|----------|
| **联调真源** | Flask :5200 + portal :3000 + WP :8800 | ✅ 第一轮诗词+WP REST 已跑通 |
| **诗词注入** | `import_poetry.py` → looma.db | ⚠️ Chroma 版本阻塞；现有 **58059** 条可用 |
| **shared-core** | S0-3 题库/人格/IDENTITY_LABELS | ✅ 已编码，待 push |
| **planetx** | 报告 #2 迁移 import shared-core | ✅ 已做 |
| **miniprogram** | 报告 #1 npm 接入 | W2 待做 |
| **合规** | 报告 #3 miniprogram consent | W3 待做 |
| **CORS** | 生产 `.env` 含 szbolent.cn | ✅ example+config 已改 |
| **烟雾测试** | verify-closed-loop + poetry | ✅ 已扩展 |
| **RFC** | `/v1/poetry/authors` | ✅ 已实现（szbenyx `27762f5`） |
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
| **P0** | push looma + portal（含 ROUND1 报告） | 供 szbenyx Review |
| **P1** | Chroma import 或确认 58k 基线 | 见 ROUND1 R1-D1 |
| **P1** | WP uploads + 较新 SQL | Blog 内容 |
| **P1** | push 后请 szbenyx Review shared-core PR | |
| **P1** | 生产机 `CORS_ORIGINS` 写入真实 `.env` | 非 example |
| **P2** | miniprogram npm + consent（W2–W3） | |

---

## 5. 文档真源位置

| 文档 | 真源 |
|------|------|
| `DECISION_RESPONSE.md` | 远端 szbenyx 版 + 本地 amendment（§四/§六） |
| `JASON_DECISION_ACK.md` | Jason 确认 |
| `DUAL_REPO_WORK_GUIDE.md` | 双仓 sync（Jason 改 → push portal） |
| `DUAL_REPO_SYNC_STATUS.md` | 本文（同步状态，有冲突时以部署策略为准） |
| `ROUND1_INTEGRATION_REPORT.md` | **第一轮联调发现 + szbenyx 认领任务** |

---

## 6. 待周一 sync 确认的一点

§四 #1 与「部署策略」文字冲突：以 **诗词注入归 Jason** 为准；建议 szbenyx 下版 DECISION 删改 §四#1 与 §六末句，避免歧义。
