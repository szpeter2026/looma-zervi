#!/usr/bin/env bash
# start-local-against-cloud.sh — 本机前端 + 云 API 联调
#
# 用法:
#   ./scripts/start-local-against-cloud.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=scripts/lib/cloud-ssh-env.sh
source "$ROOT/scripts/lib/cloud-ssh-env.sh"
[ -n "$CLOUD_HOST" ] || { echo "请设置 CLOUD_HOST"; exit 1; }

export VITE_API_BASE="http://${CLOUD_HOST}"
export VITE_API_BASE_URL="http://${CLOUD_HOST}"
export VITE_SAAS_URL="${VITE_SAAS_URL:-http://localhost:5174}"

cd "$ROOT/frontend"

echo "PlanetX / SaaS 将请求云 API: ${VITE_API_BASE}"
echo "按 Ctrl+C 停止"

pnpm --filter @looma/planetx dev &
PX=$!
pnpm --filter @looma/saas dev &
SX=$!
trap "kill $PX $SX 2>/dev/null" EXIT INT TERM
wait
