# Migration Guide - Source Code to Framework

> This document maps existing source files to their new locations in the looma-zervi framework.

## Phase 1: Backend migration

### 1.1 Auth module (from Tatha/DemoPeter)

| Source file | Target | Notes |
|---|---|---|
| `auth_routes.py` (431 lines) | `backend/src/api/routes/auth_routes.py` | Already scaffolded with new JWT flow. Migrate register/login logic, replace AUTH_STUB with real JWT |
| `auth.py` (193 lines) | `backend/src/api/auth/jwt_handler.py` + `decorators.py` | Already scaffolded. Replace _verify_token_stub with PyJWT verification |
| `supabase_client.py` (221 lines) | DELETE | Supabase dependency removed in MVP |
| `manager.py` SCHEMA_SQL | `backend/src/db/manager.py` | Already scaffolded with full schema. Add `wechat_openid` field (done), remove `supabase_uid` (not needed in MVP) |

### 1.2 Business routes

| Source endpoint | Target file | Migration notes |
|---|---|---|
| `/v1/ask` | `ask_routes.py` | Migrate ask.py: ChromaDB search → DeepSeek completion → streaming response |
| `/v1/jobs/*` | `jobs_routes.py` | Migrate job listing + matching logic |
| `/v1/resume/*` | `resume_routes.py` | Migrate resume upload + parsing pipeline |
| `/v1/reports/*` | `reports_routes.py` | Migrate daily/weekly/monthly report generation |
| `/v1/game/*` | `game_routes.py` | NEW - build from scratch (personality, fleet, mission) |
| `/v1/enterprise/*` | `enterprise_routes.py` | NEW - build from scratch (HR management) |
| `/v1/referral/*` | `referral_routes.py` | NEW - build from scratch (referral links) |

### 1.3 RAG module

| Source | Target | Notes |
|---|---|---|
| ChromaDB client code | `backend/src/rag/chroma_client.py` | Already scaffolded. Migrate collection config + search logic |
| Embedding generation | `backend/src/rag/embeddings.py` | Migrate from DemoPeter (Ollama or DeepSeek embeddings) |
| DeepSeek client | `backend/src/agents/deepseek_client.py` | Already scaffolded. Migrate chat_completion + rag_answer |

### 1.4 Database

| Source | Target | Notes |
|---|---|---|
| `manager.py` (existing) | `backend/src/db/manager.py` | Already scaffolded with full schema. Migrate CRUD operations table by table |
| Poetry RAG (78656 entries) | ChromaDB | Re-import after ChromaDB container is running |

## Phase 2: Frontend migration

### 2.1 shared-core (from @looma/shared)

| Source | Target | Notes |
|---|---|---|
| `endpoints.ts` (138 lines) | `shared-core/src/api/createApi.ts` | Only migrate createAuthApi. Other modules go to saas package |
| `ApiClient` | `shared-core/src/api/ApiClient.ts` | Already scaffolded with axios + JWT interceptor |
| Type definitions | `shared-core/src/types/auth.ts` | Already scaffolded. Add personality/result types as needed |
| Constants | `shared-core/src/constants/` | Already scaffolded with API_ROUTES + QUOTA_LIMITS |

### 2.2 PlanetX (from packages/web PlanetX code)

| Source | Target | Notes |
|---|---|---|
| `pages/planetx/*` (7 screens) | `planetx/src/features/*/` | Split by feature: quiz, fleet, profile |
| `components/planetx/*` (6 components) | `planetx/src/brand/components/` | StarBackground, XPBar, etc. |
| `planetxStore.ts` | `planetx/src/features/auth/planetxAuthStore.ts` | Already scaffolded. Remove Supabase imports, use looma JWT |
| `types/planetx.ts` | `planetx/src/features/*/types.ts` | Split per feature |
| PlanetX CSS in globals.css | `planetx/src/brand/tokens.css` + `animations.css` | Already scaffolded with game theme |

### 2.3 SaaS (from packages/web SaaS code)

| Source | Target | Notes |
|---|---|---|
| `pages/panel/*` | `saas/src/features/*/` | Split by feature: dashboard, hr, chat, enterprise |
| `authStore.ts` | `saas/src/features/auth/authStore.ts` | Already scaffolded with looma JWT |
| `AuthGuard` | `saas/src/features/auth/SaasAuthGuard.tsx` | Already scaffolded |
| `Sidebar` + layout | `saas/src/brand/components/AppLayout.tsx` | Already scaffolded with sidebar + header |
| `tokens.css` | `saas/src/brand/tokens.css` | Already scaffolded with SaaS theme |
| SaaS CSS in globals.css | `saas/src/styles/globals.css` | Already scaffolded |

### 2.4 Miniprogram (from existing miniprogram)

| Source | Target | Notes |
|---|---|---|
| Native shell (~200 lines) | `miniprogram/app.ts` | Already scaffolded with auto-login flow |
| Login flow | `miniprogram/pages/index/index.ts` | Already scaffolded. Migrate invite code validation |
| web-view wrapper | TBD | Migrate web-view pointing to planetx.genz.ltd |

## Phase 3: CloudBase setup

1. Create CloudBase environment (free tier)
2. Deploy `wechat-login` pass-through function
3. Configure miniprogram domain whitelist:
   - api.genz.ltd (looma backend)
   - CloudBase default domain
4. Set up customer service (客服)
5. Test openid login flow end-to-end

## Migration priority

| Priority | What | Why |
|---|---|---|
| P0 | Backend auth (JWT + wechat) | Everything depends on auth |
| P0 | DB schema + user table | Auth needs user table |
| P1 | /v1/ask (RAG) | Core product feature |
| P1 | PlanetX frontend migration | C-end user experience |
| P2 | SaaS frontend migration | B-end user experience |
| P2 | /v1/game/* endpoints | C-end gamification |
| P3 | /v1/enterprise/* endpoints | B-end enterprise features |
| P3 | Miniprogram polish | Conversion optimization |
