#!/usr/bin/env bash
# test-cloud-connectivity.sh — 本机 → 云内测 API 联网验收
#
# 用法:
#   ./scripts/test-cloud-connectivity.sh
#   API_BASE=http://1.14.202.161 ./scripts/test-cloud-connectivity.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=scripts/lib/cloud-ssh-env.sh
source "$ROOT/scripts/lib/cloud-ssh-env.sh"
API_BASE="${API_BASE:-http://${CLOUD_HOST}}"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
pass() { echo -e "${GREEN}✅${NC} $1"; }
fail() { echo -e "${RED}❌${NC} $1"; exit 1; }

[ -n "$CLOUD_HOST" ] || fail "请设置 CLOUD_HOST"

echo "🔗 云内测联网验收 — ${API_BASE}"
echo "=========================================="

echo -n "1. Health ... "
body=$(curl -sf --connect-timeout 10 "${API_BASE}/health") || fail "无法访问 ${API_BASE}/health（检查安全组 80、Nginx、gunicorn）"
echo "$body" | grep -q looma-backend && pass "$body" || fail "health 响应异常: $body"

echo -n "2. 诗词 random ... "
curl -sf --connect-timeout 15 "${API_BASE}/v1/poetry/random?count=1" | grep -q . && pass "OK" || fail "poetry API 失败"

echo ""
echo "3. P0 合规烟雾（公网 API）..."
API_BASE="$API_BASE" "$ROOT/scripts/verify-p0-local.sh"

echo ""
echo "4. 闭环烟雾..."
API_BASE="$API_BASE" "$ROOT/scripts/verify-closed-loop.sh"

echo ""
pass "云 ↔ 本机联网验收通过"
echo ""
echo "本地前端指向云 API 启动:"
echo "  VITE_API_BASE=${API_BASE} pnpm --filter @looma/planetx dev"
echo "  VITE_API_BASE=${API_BASE} pnpm --filter @looma/saas dev"
