# 双仓远端同步状态与职责对照

> **更新：** 2026-07-04 晚 · Jason push 后 · **szbenyx 请阅 §0 + §7**  
> **联调报告：** [ROUND1_INTEGRATION_REPORT.md](./ROUND1_INTEGRATION_REPORT.md)（含 **§8 补充通知**）  
> **远端 HEAD：** [looma `refactor/framework-v2` @ `52cf717`](https://github.com/szpeter2026/looma-zervi/tree/refactor/framework-v2) · [portal `main` @ `7d7d370`](https://github.com/szpeter2026/szbolent-portal)

---

## 0. 给 szbenyx 的三条必读

1. **请 pull 两仓**（见 ROUND1 **§8.1**），阅读 **ROUND1 §8** 全文。  
2. **looma 合并：** 请 Review PR **`refactor/framework-v2` → `main`**（含 S0-3、ROUND1 文档、CI 修复）。  
3. **分支保护：** GitHub 提示 `main` 未保护 — 请为 **两仓 `main`** 启用 PR + required checks（见 ROUND1 **§8.2**）。

---

## 1. 远端推送摘要（最新）

| 仓 | 分支 | Commit | 作者 | 内容 |
|----|------|--------|------|------|
| **looma-zervi** | `refactor/framework-v2` | `52cf717` | Jason | saas Reports token 修复 |
| | | `1872692` | Jason | shared-core ApiClient.test typecheck |
| | | `1ac47b3` | Jason | ROUND1 报告 + sync status |
| | | `27762f5` | szbenyx | CORS、authors API、verify |
| **looma-zervi** | `main` | `27762f5` | — | **尚未含 Jason S0-3 / CI 修复** |
| **szbolent-portal** | `main` | `7d7d370` | Jason | ROUND1 + WP compose + About 修复 |
| | | `2f7a202` | szbenyx | legacy 归档 P0-P5/P0-P6 |

---

## 2. 同步状态

### looma-zervi

| 项 | 说明 |
|----|------|
| 开发分支 | `refactor/framework-v2` @ `52cf717` — **与 `github` 同步** |
| `main` | 仍 @ `27762f5` — **待 PR 合并** |
| CI | PR/push 至 `refactor/framework-v2` 跑 typecheck + pytest |

### szbolent-portal

| 项 | 说明 |
|----|------|
| `main` | @ `7d7d370` — **与 `origin` 同步** |
| Jason 已 push | ROUND1、docker-compose WP 挂载、About 占位 |

---

## 3. 第一轮联调结论（不变）

| 链路 | 状态 |
|------|------|
| 诗词 portal ↔ looma | ✅ 70% |
| 博客 portal ↔ WP | ⚠️ 40% |
| 活动 legacy `:8001` | ❌ 10% |

详情 → `ROUND1_INTEGRATION_REPORT.md` §2–§4。

---

## 4. szbenyx 待办（合并 ROUND1 §6.2 + §8.4）

| 优先级 | 任务 |
|--------|------|
| **P0** | Review PR looma `refactor/framework-v2` → `main` |
| **P0** | 两仓 `main` 分支保护 + required checks |
| **P0** | portal vite 清 `:8001`（P0-P4） |
| **P1** | contracts、`poetry.ts`/authors、`looma.ts`、legal |
| **P1** | 回复 ROUND1 §7 四项决策 |
| **P2** | DECISION_RESPONSE 歧义清理 · Pricing mock |

---

## 5. Jason 待办

| 优先级 | 任务 |
|--------|------|
| **P1** | Chroma import 或确认 58k 基线 |
| **P1** | WP uploads + 较新 SQL |
| **P2** | miniprogram shared-core / consent（W2–W3） |

---

## 6. 文档真源

| 文档 | 说明 |
|------|------|
| `ROUND1_INTEGRATION_REPORT.md` | 联调发现 + **§8 szbenyx 补充通知** |
| `DUAL_REPO_SYNC_STATUS.md` | 本文（远端 HEAD + 待办） |
| `DECISION_RESPONSE.md` | 决策真源（§部署策略优先） |
| `DUAL_REPO_WORK_GUIDE.md` | 双仓分工与 P0 清单 |

---

## 7. 待 Monday sync

- §7 四项 + activity P0-L6 拍板  
- 确认 szbenyx 是否采纳 portal `7d7d370` 中 `docker-compose.wp.yml` 默认值
