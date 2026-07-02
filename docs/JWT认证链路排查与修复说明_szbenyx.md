# JWT 认证链路排查与修复说明

> **受众**：@szbenyx（后端 Auth / SaaS 模块 Owner）  
> **编写**：Jason（P0 Consent UI + 闭环 E2E）  
> **日期**：2026-07-01  
> **分支**：`refactor/framework-v2`（本地，待 push）

---

## 1. 问题现象

本地访问 SaaS `http://localhost:5174/` 时，浏览器控制台出现：

```
failed to load resource: 401 (UNAUTHORIZED)
```

页面本身（Dashboard 公开路由）仍可浏览，但控制台持续报错，且存在「已登录 UI 但实际 token 已失效」的风险。

---

## 2. 根因分析（前后端链路）

### 2.1 前端：401 清理不一致（P0 主因）

| 现象 | 原因 |
|------|------|
| 控制台 401 | App mount 时 `tryAutoLogin()` → `GET /v1/auth/profile`，localStorage 中 **过期/跨环境** token 被后端拒绝 |
| 「假登录」 | `ApiClient` 401 时只清 `looma_token`；`saas-auth`（Zustand persist）仍保留 token；多数页面 **未挂** `onUnauthorized → logout()` |
| 双 token 源 | `saas-auth` + `looma_token` + 部分页面直读 localStorage（如 `useChat.ts`） |

**典型触发条件**：
- 曾连接线上 `api.genz.ltd`，本地仍留旧 JWT
- 本地 `JWT_SECRET` 与签发 token 的环境不一致
- token 超过 `JWT_EXPIRY_HOURS`（默认 24h）未 refresh

### 2.2 后端：JWT 有效 ≠ 用户仍有效（P1）

`@require_auth` **原先**仅 `verify_token()`，从 JWT 读取 `tier`，**不查 DB**：

- 用户被删后，旧 JWT 在过期前仍可用于 game / enterprise / credit 等
- `payment/upgrade` 只更新 DB tier，**不签发新 JWT** → 配额/限流仍读 JWT 内旧 tier
- `narrative/stats` 检查 `g.user_role`，但 decorator 从未设置 → admin 也 403

### 2.3 `@optional_auth` 的静默降级

`/v1/ask`、analytics 等：无效 token **不返回 401**，降级为 `guest-{uuid}`。  
前端无法感知「token 已失效」，埋点 user 关联可能丢失。

---

## 3. 本次已实施修复（P0 → P1）

### P0 — 前端统一 ApiClient + session 恢复

| 改动 | 文件 |
|------|------|
| 新增 SaaS 统一工厂 `createSaasApiClient()`，401 → `logout()` | `frontend/packages/saas/src/api/saasApiClient.ts` |
| 所有 SaaS 业务页改走统一工厂（Jobs / Resume / Poetry / Reports / Pricing / Candidates / analytics / MicroFeedbackBar 等） | 见 git diff |
| `authStore`：`fetchProfile` / `tryAutoLogin` 失败 → 完整 `logout()`；新增 `applySessionToken()` | `frontend/packages/saas/src/features/auth/authStore.ts` |
| PlanetX `checkSession` 从 `looma_token` 恢复内存 token | `frontend/packages/planetx/src/features/auth/planetxAuthStore.ts` |
| PlanetX analytics / feedback 改走 `getApiClient()`（含 onUnauthorized） | `usePlanetXAnalytics.ts`、`PlanetXMicroFeedback.tsx`、`FeedbackSurvey.tsx` |
| Dashboard `/health` 不带 Authorization（避免 stale token 干扰） | `Dashboard.tsx`（前序 commit） |

### P1 — 后端 DB 同步 + tier 升级发新 token

| 改动 | 文件 |
|------|------|
| `@require_auth`：JWT 校验后 **`get_user_by_id`**，同步 `g.user_tier` / `g.user_role` from DB；用户不存在 → **401** | `backend/src/api/auth/decorators.py` |
| 新增 `sign_token_for_user(db, user_id)`，从 DB 签发 JWT | `backend/src/api/auth/jwt_handler.py` |
| `POST /v1/payment/upgrade` 响应增加 **`access_token`** | `backend/src/api/routes/payment_routes.py` |
| `POST /v1/referral/use` 若 tier 变更，同样返回 **`access_token`** | `backend/src/api/routes/referral_routes.py` |
| `/v1/auth/refresh` 改用 `sign_token_for_user` | `backend/src/api/routes/auth_routes.py` |
| Pricing 升级后 `applySessionToken(resp.access_token)` | `frontend/packages/saas/src/features/pricing/Pricing.tsx` |
| 类型 `UpgradeResponse` 增加可选 `access_token` | `frontend/packages/shared-core/src/types/payment.ts` |
| 新增测试：删用户后 401、upgrade 返回新 tier token | `backend/tests/test_auth.py` |

**`narrative/stats`**：无需改路由代码；`@require_auth` 现已设置 `g.user_role`，admin 可正常访问。

---

## 4. 修复后链路（目标状态）

```
登录/注册 → sign_token(user_id, tier from DB)
     ↓
前端存 token：saas-auth + looma_token（双写，logout 双清）
     ↓
受保护请求 → @require_auth
     ├─ verify_token (签名/exp/iss)
     ├─ get_user_by_id → 401 if missing
     └─ g.user_tier / g.user_role ← DB（非 JWT 声明）
     ↓
401 → ApiClient → onUnauthorized → logout()（SaaS/PlanetX 统一）
     ↓
tier 变更 → 响应带 access_token → applySessionToken()
```

---

## 5. 本地验证步骤

```bash
# 1. 清 stale token（浏览器控制台）
localStorage.removeItem('saas-auth');
localStorage.removeItem('looma_token');
location.reload();

# 2. 后端
cd backend && bash dev.sh   # → :5200

# 3. 前端
cd frontend && VITE_API_BASE=http://localhost:5200 pnpm dev:saas   # → :5174

# 4. 后端测试
cd backend && source venv/bin/activate
pytest tests/test_auth.py -v
```

**预期**：
- 首页无 profile 401 噪音（无 token 时不请求 profile）
- 登录后 Jobs / Resume / Pricing 试用正常
- Pricing「开始 7 天试用」后 quota 立即反映 Pro tier

---

## 6. 仍未覆盖（P2，建议 szbenyx 评审）

| 项 | 说明 | 建议 Owner |
|----|------|------------|
| Token 主动 refresh | 前端仍不 decode `exp`，未定时调 `/v1/auth/refresh` | JOINT |
| Logout / token 吊销 | 无 blacklist，refresh 后旧 token 仍有效至 exp | szbenyx |
| `@optional_auth` 过期 token | 仍静默 guest，不 401 | szbenyx |
| `@require_consent` 覆盖 | 仅 credit 路由 enforce；resume/ask/jobs 仅前端 UI | JOINT |
| `useChat.ts` SSE | 直读 `saas-auth`，未走统一 client | Jason |
| 跨 port SSO | PlanetX :5173 / SaaS :5174 localStorage 隔离 | 部署层同域解决 |
| 生产 JWT_SECRET | 默认 secret 仍存在 | szbenyx / DevOps |

---

## 7. szbenyx 需关注的后端契约变更

1. **`@require_auth` 每次请求多一次 DB 读** — 内测可接受；高 QPS 时可改为 Redis 缓存 user meta 或短 TTL。
2. **`POST /v1/payment/upgrade` 响应新增字段**：
   ```json
   {
     "tier": "pro",
     "access_token": "...",
     "token_type": "bearer",
     "expires_in": 86400,
     ...
   }
   ```
3. **`POST /v1/referral/use`**：仅当 invite 的 `tier_grant` 实际更新了 users.tier 时，才附带 `access_token`。
4. **破坏性**：已删除用户的 JWT 现在会 **401**（原先可能仍 200）。

---

## 8. 相关文件索引

**后端**
- `backend/src/api/auth/decorators.py`
- `backend/src/api/auth/jwt_handler.py`
- `backend/src/api/routes/auth_routes.py`
- `backend/src/api/routes/payment_routes.py`
- `backend/src/api/routes/referral_routes.py`
- `backend/tests/test_auth.py`

**前端**
- `frontend/packages/saas/src/api/saasApiClient.ts`
- `frontend/packages/saas/src/features/auth/authStore.ts`
- `frontend/packages/planetx/src/features/auth/planetxAuthStore.ts`
- `frontend/packages/shared-core/src/api/ApiClient.ts`
- `frontend/packages/shared-core/src/types/payment.ts`

---

如有疑问或需调整 `@require_auth` 的 DB 查询策略，请在 PR review 中 @Jason 同步。
