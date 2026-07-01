#!/usr/bin/env bash
# e2e-backend.sh — Playwright 真实后端（独立测试库，端口 5200）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

if [ -d venv ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

E2E_DB="${E2E_DATABASE_PATH:-$ROOT/backend/data/e2e-playwright.db}"
rm -f "$E2E_DB" "${E2E_DB}-wal" "${E2E_DB}-shm" 2>/dev/null || true
mkdir -p "$(dirname "$E2E_DB")"

export DATABASE_PATH="$E2E_DB"
export POETRY_CHROMA_PATH="${POETRY_CHROMA_PATH:-$ROOT/data/poetry_full}"
export FLASK_PORT="${FLASK_PORT:-5200}"
export JWT_SECRET=e2e-playwright-jwt-secret-32bytes!!
export WECHAT_DEV_MODE=true
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-skip}"
export PG_HOST="${PG_HOST:-127.0.0.1}"
export PG_PORT="${PG_PORT:-5433}"

exec python3 run.py
