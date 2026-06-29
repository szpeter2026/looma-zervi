# Looma-Zervi

> Server-Terminal architecture: Looma Python backend + Zervi frontend clients
> Dual brand: PlanetX (C-end job seekers) + T-space (B-end HR enterprises)

## Architecture overview

```
                    ┌─────────────────┐
  WeChat MiniApp ──→│  CloudBase shell │── openid ──→
                    │  (login +客服)    │
                    └─────────────────┘               ┌──────────────────┐
                                                       │  Looma Backend    │
  Web Browser ────────── HTTPS ──────────────────────→ │  Flask + JWT      │
                                                       │  ChromaDB + SQLite│
                                                       │  DeepSeek API     │
                                                       └──────┬───────────┘
                                                              │
                                          ┌───────────────────┼───────────────┐
                                          │                   │               │
                                    ┌─────┴─────┐    ┌────────┴──────┐  ┌────┴─────┐
                                    │ ChromaDB  │    │    SQLite     │  │ DeepSeek │
                                    │ (vectors) │    │ (users/games) │  │   API    │
                                    └───────────┘    └───────────────┘  └──────────┘
```

## Project structure

```
looma-zervi/
├── backend/          # Looma Python backend (Flask + ChromaDB + SQLite)
├── frontend/         # Frontend monorepo (pnpm workspace)
│   └── packages/
│       ├── shared-core/   # Shared types, API client, constants (dual-review)
│       ├── planetx/       # PlanetX C-end brand (Jason owns)
│       ├── saas/          # T-space B-end brand (szbenyx owns)
│       └── miniprogram/   # WeChat miniprogram shell (Jason owns)
├── cloudbase/        # CloudBase deployment config
├── docker/           # Docker + nginx deployment
└── docs/             # Architecture docs
```

## Auth flow (MVP - no Supabase)

| Entry point | Flow | Auth endpoint |
|---|---|---|
| WeChat MiniApp | wx.login → CloudBase openid → looma JWT | POST /v1/auth/wechat |
| Web browser | email/password → looma JWT | POST /v1/auth/login |
| Web register | email/password → looma JWT | POST /v1/auth/register |
| Cross-platform bind | wechat_openid ↔ email | POST /v1/auth/bind |
| (optional) Supabase bridge | Supabase JWT → looma JWT | POST /v1/auth/bridge |

## Quick start

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # edit config
python run.py
```

### Frontend
```bash
cd frontend
pnpm install
pnpm --filter @looma/planetx dev   # PlanetX on :5173
pnpm --filter @looma/saas dev      # T-space on :5174
```

## Ownership matrix

| Package / Route group | Owner |
|---|---|
| packages/planetx + /v1/game/* | Jason |
| packages/saas + /v1/enterprise/* | szbenyx |
| packages/shared-core + /v1/auth/* | Joint (dual review) |
| packages/miniprogram | Jason |
| /v1/jobs/*, /v1/ask, /v1/resume/*, /v1/reports/* | szbenyx |
| /v1/referral/* | Jason |

## Tech stack

- **Backend**: Python 3.10+, Flask, SQLite (WAL), ChromaDB, DeepSeek API
- **Frontend**: React 18, TypeScript, Vite, Zustand, Tailwind CSS
- **Miniprogram**: WeChat native + CloudBase
- **Deploy**: Docker + nginx on Aliyun ECS
