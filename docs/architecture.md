# Looma-Zervi Architecture

> Last updated: 2026-06-29

## 1. System overview

```
                          ┌─────────────────────┐
  WeChat MiniApp ────────→│  CloudBase shell     │
  (国内用户入口)           │  openid + 客服        │
                          └──────────┬──────────┘
                                     │ POST /v1/auth/wechat
                                     ▼
  Web Browser ──────────────────────────────────→ ┌──────────────────────┐
  (Web + SEO 获客)                                  │  Looma Backend        │
                                                   │  Flask + JWT          │
                                                   │  (阿里云 ECS)          │
                                                   └──────┬───────────────┘
                                                          │
                                       ┌──────────────────┼──────────────────┐
                                       │                  │                  │
                                 ┌─────┴─────┐   ┌────────┴────────┐  ┌─────┴──────┐
                                 │ ChromaDB  │   │     SQLite      │  │ DeepSeek   │
                                 │ (vectors) │   │  (WAL mode)     │  │ API        │
                                 │ :8000     │   │  users/games/   │  │            │
                                 └───────────┘   │  enterprise/    │  └────────────┘
                                                 │  invite_codes   │
                                                 └─────────────────┘
```

## 2. Auth flow (MVP - no Supabase)

### 2.1 WeChat MiniApp login

```
1. Client: wx.login() → gets temporary code
2. Client: POST /v1/auth/wechat { code }
3. Backend: calls WeChat API code2session(code) → gets openid
4. Backend: finds or creates user by wechat_openid
5. Backend: signs looma JWT with user_id + tier
6. Backend: returns { access_token, user }
7. Client: caches token in localStorage/storage
```

### 2.2 Web login

```
1. Client: POST /v1/auth/login { email, password }
2. Backend: bcrypt verify password
3. Backend: signs looma JWT
4. Backend: returns { access_token, user }
```

### 2.3 Cross-platform binding

```
1. User is logged in (has looma JWT) on MiniApp
2. User opens /pages/auth and enters email + password
3. Client: wx.login() → gets code
4. Client: POST /v1/auth/bind { code } (with Bearer JWT)
5. Backend: calls code2session → gets openid
6. Backend: verifies openid not bound to another user
7. Backend: UPDATE users SET wechat_openid = ? WHERE id = ?
8. Now the user can login from both Web and MiniApp
```

### 2.4 Supabase bridge (optional - not implemented in MVP)

```
1. Web user uses social login (Google/GitHub) via Supabase
2. Client gets Supabase JWT
3. Client: POST /v1/auth/bridge { token: supabase_jwt }
4. Backend: verifies Supabase JWT signature
5. Backend: looks up supabase_uid → looma user_id
6. Backend: signs looma JWT
7. Backend: returns { access_token, user }

MVP: returns 501 Not Implemented
```

## 3. Frontend monorepo structure

```
frontend/packages/
├── shared-core/     ← Contract layer (dual review)
│   ├── api/         ApiClient, createAuthApi
│   ├── types/       User, LoginResponse, Brand types
│   ├── constants/   API_ROUTES, QUOTA_LIMITS
│   └── utils/       format, validation
│
├── planetx/         ← C-end brand (Jason owns)
│   ├── features/    auth, quiz, fleet, profile
│   ├── brand/       tokens.css, animations.css, components
│   ├── styles/      globals.css
│   └── App.tsx      PlanetX routes
│
├── saas/            ← B-end brand (szbenyx owns)
│   ├── features/    auth, dashboard, hr, chat, enterprise
│   ├── brand/       tokens.css, markdown.css, AppLayout
│   ├── styles/      globals.css
│   └── App.tsx      SaaS routes
│
└── miniprogram/     ← WeChat shell (Jason owns)
    ├── pages/       index, auth
    ├── utils/       api wrapper
    └── app.ts       global state + auto-login
```

### Import rules (enforced)

```
Allowed:
  planetx → @looma/shared-core ✅
  saas    → @looma/shared-core ✅
  planetx → planetx internal   ✅
  saas    → saas internal      ✅

Forbidden:
  planetx → saas               ❌
  saas    → planetx            ❌
  any     → old @looma/shared  ❌ (deprecated)
```

## 4. Backend route ownership

| Route group | Owner | Blueprint file |
|---|---|---|
| /v1/auth/* | Joint (dual review) | auth_routes.py |
| /v1/game/* | Jason | game_routes.py |
| /v1/enterprise/* | szbenyx | enterprise_routes.py |
| /v1/ask | szbenyx | ask_routes.py |
| /v1/jobs/* | szbenyx | jobs_routes.py |
| /v1/resume/* | szbenyx | resume_routes.py |
| /v1/reports/* | szbenyx | reports_routes.py |
| /v1/referral/* | Jason | referral_routes.py |
| /v1/quota | Joint | quota_routes.py |

## 5. Database schema

See `backend/src/db/manager.py` SCHEMA_SQL for the complete schema.

Key tables and ownership:

| Table | Owner | Purpose |
|---|---|---|
| users | Joint | Core user table (email + wechat_openid) |
| game_profiles | Jason | Personality type + XP + level |
| fleets, fleet_members | Jason | Team/fleet system |
| mission_completions | Jason | Mission tracking |
| enterprises, enterprise_users | szbenyx | Enterprise/tenant |
| candidates | szbenyx | Candidate profiles (HR view) |
| invite_codes | Joint | C→B conversion tracking |
| usage_logs | Joint | Daily quota tracking |

## 6. Deployment

### Production (Aliyun ECS)

```bash
# On the server:
cd /opt/looma-zervi
docker compose -f docker/docker-compose.yml up -d --build

# Frontend builds (run locally, then deploy):
cd frontend
pnpm install
pnpm build:planetx  # → upload dist/ to /var/www/planetx/dist
pnpm build:saas     # → upload dist/ to /var/www/saas/dist
```

### Domains

| Domain | Service |
|---|---|
| api.genz.ltd | Looma backend (Flask) |
| planetx.genz.ltd | PlanetX frontend (static) |
| t.genz.ltd | T-space frontend (static) |

### CloudBase (miniprogram only)

CloudBase free tier handles:
- Miniprogram hosting
- openid login (via pass-through function → looma backend)
- Customer service integration

CloudBase does NOT handle:
- Business logic
- Database
- AI/RAG
- Payment (upgrade to standard 199/mo when needed)
