# 双仓远端同步状态与职责对照

> **更新：** 2026-07-16 · WordPress 阿里云主站部署 · 双端远端同步  
> **联调报告：** [ROUND1_INTEGRATION_REPORT.md](./ROUND1_INTEGRATION_REPORT.md)（含 **§8 补充通知**）  
> **远端 HEAD：** [looma `main`](https://github.com/szpeter2026/looma-zervi/tree/main) · [portal `main`](https://github.com/szpeter2026/szbolent-portal/tree/main)

---

## 0. 给 szbenyx 的三条必读

1. **请 pull 两仓**，阅读 **[PAYMENT_TIER_CONTRACT.md](./PAYMENT_TIER_CONTRACT.md)**（支付/tier 统一标准 · CN ¥9.9 / US $1.99）。  
2. **大陆主站：** WordPress 已部署阿里云 `47.115.168.107`（Bolent 子主题 + Podman）；Vue 门户 SPA 逐步由 WP 承接营销页。  
3. **同步命令：** 各仓 `npm run sync:push`（portal）或 `./scripts/sync-remotes.sh push`（looma，待补齐）。

---

## 1. 远端推送摘要（最新）

| 仓 | 分支 | Commit | 作者 | 内容 |
|----|------|--------|------|------|
| **looma-zervi** | `main` | `b40700d` | Jason | 双仓 sync status 文档对齐 |
| | | `11a206d` | Jason | Phase 3 纯 UI 组件库 + Storybook `:6007` |
| | | `8f08d50` | Jason | 支付契约 `payment.v1.json` + region-aware plans |
| **szbolent-portal** | `main` | `528198d` | Jason | Storybook 组件 stories + React 依赖修复 |
| | | `bfad810` | Jason | 移除 onboarding MDX 脚手架 |
| | | `cbd2d8d` | Jason | Storybook init + Astra design-system + 外包文档 |
| | | `2ed3fec` | Jason | PAYMENT_TIER_CONTRACT 双仓存档 |

---

## 2. 同步状态

### looma-zervi

| 项 | 说明 |
|----|------|
| `main` | **2026-07-05** 已与 `github/main` 同步 |
| Storybook | `frontend/` · `pnpm storybook` → **:6007** |
| 支付真源 | `backend/contracts/payment.v1.json` · `GET /v1/payment/plans?region=CN\|US` |

### szbolent-portal

| 项 | 说明 |
|----|------|
| `main` | 待推送：WP 生产部署脚本 + GitHub/Gitee 同步工具 |
| WordPress | 阿里云 `47.115.168.107` · `/opt/bolent-wp` · Bolent Astra Child |
| 同步 | `npm run sync:push` → `origin` + `gitee`；CI `sync-to-gitee.yml` |
| Storybook | `npm run storybook` → **:6006** |

---

## 3. 第一轮联调结论（不变）

| 链路 | 状态 |
|------|------|
| 诗词 portal ↔ looma | ✅ 70% |
| 博客 portal ↔ WP | ⚠️ 40% |
| 活动 legacy `:8001` | ❌ 10% |

详情 → `ROUND1_INTEGRATION_REPORT.md` §2–§4。

---

## 4. szbenyx 待办

| 优先级 | 任务 |
|--------|------|
| **P0** | 两仓 `main` 分支保护 + required checks |
| **P0** | portal vite 清 `:8001`（P0-P4） |
| **P1** | portal 接 `looma.ts` + Pricing（**PAYMENT_TIER_CONTRACT §6.2**） |
| **P1** | Astra 外包 Phase 1–4（见 portal 外包交付文档） |
| **P1** | contracts、`poetry.ts`/authors、legal |
| **P2** | DECISION_RESPONSE 歧义清理 |

---

## 5. Jason 待办

| 优先级 | 任务 |
|--------|------|
| **P1** | looma Phase 4 Storybook 七态走查（`:6007`） |
| **P1** | P1 微信支付替换 Stub |
| **P1** | Chroma import 或确认 58k 基线 |
| **P1** | WP uploads + 较新 SQL |
| **P2** | miniprogram shared-core / consent（W2–W3） |

---

## 6. 文档真源

| 文档 | 说明 |
|------|------|
| **`PAYMENT_TIER_CONTRACT.md`** | 支付/tier 契约（双仓同文） |
| `DUAL_REPO_SYNC_STATUS.md` | 本文（远端 HEAD + 待办） |
| `DUAL_REPO_WORK_GUIDE.md` | 双仓分工与 P0 清单 |
| `ROUND1_INTEGRATION_REPORT.md` | 联调发现 + §8 补充通知 |
| portal `docs/szbolent-portal-outsourcing-astra-deliverables.md` | Astra 门户外包交付 |
| looma `frontend/looma-zervi-design-outsourcing-deliverables.md` | Looma 设计外包交付 |
