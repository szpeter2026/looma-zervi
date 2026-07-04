# 第一轮双仓联调报告（Jason 本机 · 2026-07-04）

> **目的：** 记录 Jason 高性能机第一轮 **looma-zervi × szbolent-portal × WordPress** 联调发现，供 **szbenyx** 参与改进双仓体系体验。  
> **同步：** 本文与 `looma-zervi/docs/ROUND1_INTEGRATION_REPORT.md` **同文同版**（改任一侧须 sync 另一侧）  
> **关联：** [DECISION_RESPONSE.md](./DECISION_RESPONSE.md) · [DUAL_REPO_WORK_GUIDE.md](./DUAL_REPO_WORK_GUIDE.md) · [DUAL_REPO_SYNC_STATUS.md](./DUAL_REPO_SYNC_STATUS.md)

---

## 1. 联调环境快照

| 服务 | 地址 | 状态（第一轮结束时） |
|------|------|----------------------|
| Looma API | `http://127.0.0.1:5200` | ✅ 运行 |
| Portal dev | `http://127.0.0.1:3000` | ✅ 运行 |
| WordPress | `http://127.0.0.1:8800` | ✅ Docker 运行 |
| MySQL（WP） | `127.0.0.1:3307` | ✅ Docker 运行 |
| ChromaDB 向量（诗词 search） | `data/poetry_full` | ⚠️ 客户端版本不兼容，见 §3 |

**本机数据：** `backend/data/looma.db` 已有 **58,059** 首诗词、**5,146** 位作者（非空库；`import_poetry.py` 因 Chroma 格式未重跑完）。

**Git 对齐（联调前）：**

| 仓 | 关键 commit | 说明 |
|----|-------------|------|
| looma-zervi | `27762f5`（szbenyx）+ Jason 本地 merge `fb31eaf` | CORS、authors API、verify 脚本 |
| szbolent-portal | `2f7a202`（szbenyx legacy 归档）+ Jason docs merge | P0-P5/P0-P6 |

---

## 2. 已通过验收（✅）

### 2.1 Looma API（`:5200`）

| 检查项 | 结果 |
|--------|------|
| `GET /health` | ✅ |
| `GET /v1/poetry/stats` | ✅ total=58059 |
| `GET /v1/poetry/browse` | ✅ |
| `GET /v1/poetry/random` | ✅ |
| `GET /v1/poetry/authors` | ✅ 5146 位（szbenyx `27762f5`） |
| `GET /v1/poetry/search?q=明月` | ✅ SQLite 关键词回退 |
| `scripts/verify-closed-loop.sh` | ✅ 含 HR 闭环 + 诗词 P0-L4 + 诗人 P1-L1 |

### 2.2 Portal × Looma（诗词链路）

| 检查项 | 结果 |
|--------|------|
| Vite proxy `/v1` → `:5200` | ✅ |
| `curl :3000/v1/poetry/stats` | ✅ |
| 页面 `/poetry/list` HTTP 200 | ✅ |
| CORS（portal `:3000`） | ✅ 本机 `.env` 已补 |

### 2.3 Portal × WordPress（博客链路）

| 检查项 | 结果 |
|--------|------|
| Docker `docker-compose.wp.yml` + Poetry-modown `wp-content` 挂载 | ✅ |
| SQL 导入 `modown_wp_backup_2026-01-23` | ✅ |
| `GET :8800/wp-json/wp/v2/categories` | ✅ |
| `GET :3000/wp-json/wp/v2/posts`（portal 代理） | ✅ |
| 插件 **erphpdown** 激活、**modown** 主题 | ✅ |
| WP 管理员 | 用户 `zervi`（本地密码已重置，见 §5） |

### 2.4 szbenyx 已交付且验证有效

- looma：`P0-L1` CORS、`P1-L1` `/authors`、`P0-L4` verify 扩展  
- portal：`P0-P5/P0-P6` legacy 归档（`business.ts` / `tatha.ts` / `activity.ts` 标记）

---

## 3. 发现的问题（⚠️ / ❌）

### 3.1 数据与脚本

| ID | 问题 | 影响 | 建议 Owner |
|----|------|------|------------|
| **R1-D1** | `import_poetry.py` 读 `data/poetry_full` 失败（chromadb **0.6.3** vs 旧库 `KeyError: '_type'`） | 无法从 Chroma 重灌至 78656；当前靠历史 looma.db **58059** 条 | **Jason** 跑通 import 或文档化「可接受 58k」；**szbenyx** 在 `requirements.txt` 注明兼容版本或迁移脚本 |
| **R1-D2** | `/v1/poetry/search` 语义检索依赖 Chroma；失败时仅靠 SQLite 关键词 | 搜索质量下降 | **Jason** 修 Chroma 路径/版本；**szbenyx** contracts 里区分 search 两种模式 |

### 3.2 Portal 前端体验

| ID | 问题 | 影响 | 建议 Owner |
|----|------|------|------------|
| **R1-P1** | `vite.config.ts` 仍保留 `/api` → `:8001` | 活动页仍打 legacy；新人易混淆 | **szbenyx** P0-P4 删除或文档化过渡 |
| **R1-P2** | `poetry.ts` 的 `getPoets` 仍客户端扫 browse，未用 `/authors` | 诗人列表慢、与后端重复 | **szbenyx** P1-P1 改接 `/authors` |
| **R1-P3** | 无 `looma.ts`、Pricing、legal 静态页 | 认证/支付/备案路径未通 | **szbenyx** P0-P2/P0-P3/P0-P7 |
| **R1-P4** | `About.vue` 外链 `via.placeholder.com` TLS 失败 | Console 报红（已改 CSS 占位，**未 push**） | **Jason** push；**szbenyx** Review |
| **R1-P5** | 无 `favicon.ico` | 404 噪音 | 任一方补 `public/favicon.ico` |

### 3.3 WordPress 第三服务

| ID | 问题 | 影响 | 建议 Owner |
|----|------|------|------------|
| **R1-W1** | 备份仅 **1 篇文章**、**uploads/** 未入库 | Blog 空、媒体裂图 | **Jason** 拉 uploads + 新 SQL；**szbenyx** 文档写清 WP 运维边界 |
| **R1-W2** | ErphpDown 支付/证书未配 | 插件「能加载」但不能端到端付 | **Jason** 本机 Stub；**szbenyx** 与 Looma payment 策略对齐 |
| **R1-W3** | `docker-compose.wp.yml` 默认未挂 Poetry-modown（Jason 本机已改 bind mount） | 新人 `compose up` 得到空 WP | **szbenyx** 合并 compose 默认值 + README 一键步骤 |
| **R1-W4** | 备份 `siteurl` 曾为 `genz.ltd` | 需手动 UPDATE | compose 加 init 脚本或文档 |

### 3.4 双仓协作体验（给 szbenyx 的重点）

| ID | 问题 | 影响 | 建议 |
|----|------|------|------|
| **R1-X1** | 三服务启动分散（looma / portal / docker wp），无统一脚本 | 联调门槛高 | **szbenyx** 增 `scripts/dev-all.sh` 或文档「Terminal 1/2/3」 |
| **R1-X2** | `DUAL_REPO_SYNC_STATUS.md` 与真实进度滞后 | 远端/本地认知不一致 | 每轮联调后更新 + 周一 sync |
| **R1-X3** | 无 `backend/contracts/*.json` | portal 只能手写类型 | **szbenyx** W1 契约首版 |
| **R1-X4** | Jason 本地 looma 大量 commit **未 push** | szbenyx 无法 Review S0-3 | **Jason** push `refactor/framework-v2` |
| **R1-X5** | Blog 500 易被误认为「双仓联调失败」 | 体验差 | **文档**明确：诗词 / 博客 / 活动 三条独立链路 |

---

## 4. 三链路成熟度（第一轮结论）

```
诗词  portal :3000 ──/v1──► looma :5200 ──► looma.db
      成熟度：███████░░  70%   ← 主路径已通，authors/contract/58k 数据待完善

博客  portal :3000 ──/wp-json──► WP :8800 ──► MySQL
      成熟度：████░░░░░░  40%   ← API 通，内容与 ErphpDown 配置空

活动  portal ──/api──► legacy :8001
      成熟度：█░░░░░░░░░  10%   ← 未决策，仍 legacy
```

**第一轮「双仓联调」判定：** 诗词链路 **通过**；博客 **基础设施通过、内容未通过**；活动 **不在本轮范围**。

---

## 5. 本地密钥与运维备忘（仅 Jason 本机）

| 项 | 值 |
|----|-----|
| WP 登录 | http://localhost:8800/wp-login.php |
| WP 用户 | `zervi` / `347399@qq.com` |
| WP 本地临时密码 | `SzbolentLocal2026!`（**仅 Docker 开发**，请登录后修改） |
| WP SQL 来源 | `~/Downloads/modown_wp_backup_2026-01-23_12-41-35.sql` |
| Poetry-modown 路径 | `/Users/jason/SurfaceZervi/GitHub/szjason72/Poetry-modown/public/wp-content` |

> ⚠️ 勿将 WP 密码写入 git；生产环境另议。

---

## 6. 后续任务分工（请 szbenyx 认领 §6.2）

### 6.1 Jason — 下一轮（W1）

| 优先级 | 任务 | 产出 |
|--------|------|------|
| P0 | push looma `refactor/framework-v2`（S0-3、CORS、docs） | PR 供 Review |
| P0 | 解决 Chroma import 或确认 58k 为联调基线 | looma.db 状态文档化 |
| P1 | push portal（About 占位修复、compose 改动、本文） | origin/main |
| P1 | 拉取 WP `uploads/` + 较新 SQL（若有） | Blog 有内容 |
| P2 | portal `poetry.ts` 接 `/authors`（可与 szbenyx 协作） | 诗人页性能 |

### 6.2 szbenyx — 改善双仓体验（请回复认领）

| 优先级 | 任务 | 对应发现 | 预估 |
|--------|------|----------|------|
| **P0** | 合并 `docker-compose.wp.yml` Poetry-modown 挂载 + `WORDPRESS_TABLE_PREFIX=genz_` | R1-W3 | 0.5h |
| **P0** | portal P0-P4：删 vite `/api` → `:8001` 或 gated 注释 | R1-P1 | 0.5h |
| **P0** | `INTEGRATION.md` / README：三链路启动顺序 + 常见 Console 误报 | R1-X1, R1-X5 | 0.5h |
| **P1** | `poetry.ts` → `/v1/poetry/authors` | R1-P2 | 0.5d |
| **P1** | `backend/contracts/poetry.v1.json` 首版（对照已跑通 API） | R1-X3 | 0.5d |
| **P1** | `looma.ts` 薄封装 + legal 页骨架 | R1-P3 | 1d |
| **P2** | Pricing UI mock + activity P0-L6 决策落地 | DECISION §四 | 1–2d |
| **P2** | Review Jason shared-core PR；更新 `DECISION_RESPONSE` §四/§六 歧义 | R1-X2 | sync 时 |

### 6.3 联合验收（第二轮目标）

```bash
# 三服务健康
curl -sf http://127.0.0.1:5200/health
curl -sf http://127.0.0.1:8800/wp-json/wp/v2/posts?per_page=1
curl -sf http://127.0.0.1:3000/v1/poetry/stats

# 门户页面（人工）
# /poetry/list  有列表
# /blog         有 ≥3 篇文章
# Console       无 legacy :8001 误请求（活动页除外）
```

---

## 7. 请 szbenyx 反馈（周一 sync 或 PR 评论）

1. §6.2 任务优先级是否调整？  
2. `contracts/poetry.v1.json` 是否以 Jason 本机 **58059 条** 响应为 schema 真源？  
3. WordPress 运维（SQL/uploads/ErphpDown）是否仍归 Jason 本机，还是 Surface 分担？  
4. activity 模块：**迁移 Looma** vs **portal 下线** — 请拍板 P0-L6。

---

## 8. 补充通知 szbenyx（2026-07-04 · Jason 推送后）

> **本文档与 `DUAL_REPO_SYNC_STATUS.md` 已 push 至双仓远端。** 请 pull 后在本节或 PR 评论回复认领情况。

### 8.1 远端已推送（请 pull）

| 仓 | 分支 | HEAD | 要点 |
|----|------|------|------|
| **looma-zervi** | `refactor/framework-v2` | `52cf717` | ROUND1 报告 · S0-3 merge · **CI typecheck 修复** |
| **szbolent-portal** | `main` | `7d7d370` | ROUND1 报告 · **WP compose 默认挂载 Poetry-modown** · About 占位图修复 |

```bash
# szbenyx Surface 建议执行
cd looma-zervi && git fetch github && git checkout refactor/framework-v2 && git pull github refactor/framework-v2
cd szbolent-portal && git pull origin main
```

### 8.2 CI 与合并流程（重要）

- looma **开发分支**：`refactor/framework-v2`（`github` 远端已对齐 `52cf717`）
- **`main` 尚未合并** Jason 侧 S0-3 / 文档 / CI 修复；请 szbenyx **开 PR**：`refactor/framework-v2` → `main` 并 **Review**
- CI 工作流 `.github/workflows/ci.yml` 已在 PR / push 时跑：
  - `Frontend Typecheck` · `Frontend Unit Tests` · `Backend Tests` ·（可选）E2E / Docker
- Jason 已修 CI 阻断项：
  - `1872692` shared-core `ApiClient.test.ts` localStorage mock
  - `52cf717` saas `Reports.tsx` 缺失 `token` 引用
- **GitHub 提示 `main` 未保护**：请 szbenyx 在 **Settings → Branches** 为 `main`（两仓）启用：
  - Require PR before merging
  - Require status checks（至少上述三项 Frontend/Backend）
  - Block force push / deletion

### 8.3 portal 侧 Jason 已代做（请 szbenyx 确认/合并思路）

| 项 | 状态 | szbenyx 动作 |
|----|------|--------------|
| `docker-compose.wp.yml` bind mount Poetry-modown + `genz_` 表前缀 | ✅ 已在 `7d7d370` | Review 路径默认值是否适合 Surface；或改 `POETRY_MODOWN_WP_CONTENT` env |
| `About.vue` 外链占位 TLS 报错 | ✅ 已改 CSS 占位 | 可选补真实 about 图 |
| ROUND1 §6.2 **R1-W3** | ⚠️ Jason 本机先落地 | 请确认是否采纳为仓库默认 |

### 8.4 仍待 szbenyx（§6.2 不变 + 新增）

| 优先级 | 任务 |
|--------|------|
| **P0** | Review + merge PR `refactor/framework-v2` → `main`（looma） |
| **P0** | 两仓 `main` 分支保护规则 |
| **P0** | portal P0-P4 清 vite `:8001` |
| **P1** | `poetry.ts` → `/authors` · `contracts/poetry.v1.json` · `looma.ts` + legal |
| **P1** | 回复 §7 四项决策（契约真源 58k、WP 运维边界、activity 拍板） |
| **P2** | 更新 `DECISION_RESPONSE` §四/§六 与部署策略一致 |

### 8.5 WordPress 本地（Jason 机已验证 · 供 Surface 复现）

详见 portal `docker-compose.wp.yml` + ROUND1 §5。要点：

- `docker compose -f docker-compose.wp.yml up -d` → `:8800`
- 需导入 SQL（Jason 用 `~/Downloads/modown_wp_backup_2026-01-23_*.sql`）
- 插件 **erphpdown** + 主题 **modown** 随 Poetry-modown `wp-content` 挂载
- **勿将 WP 密码提交 git**；本地管理员 `zervi`，密码 Jason 本机单独维护

---

**Jason** · 2026-07-04 · 第一轮联调记录  
**待 szbenyx：** §8.2 PR Review · §8.4 认领 · §7 四项反馈
