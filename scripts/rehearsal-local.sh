#!/usr/bin/env bash
# rehearsal-local.sh — 本地彩排：持久化 + 闭环 + RAG 置信度
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_BASE="${API_BASE:-http://127.0.0.1:5200}"
BACKEND_PID=""
STARTED_BACKEND=0
LOOMA_DB="$ROOT/backend/data/looma.db"
POETRY_CHROMA="$ROOT/data/poetry_full"

# 加载根目录 .env（API key / pgvector），但彩排始终用真实数据路径
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

export DATABASE_PATH="${REHEARSAL_DATABASE_PATH:-$LOOMA_DB}"
export POETRY_CHROMA_PATH="${REHEARSAL_POETRY_CHROMA:-$POETRY_CHROMA}"
export PG_HOST="${PG_HOST:-127.0.0.1}"
export PG_PORT="${PG_PORT:-5433}"
export PG_USER="${PG_USER:-jason}"
export PG_PASSWORD="${PG_PASSWORD:-ServBay.dev}"
export PG_DATABASE="${PG_DATABASE:-looma}"

cleanup() {
  if [ "$STARTED_BACKEND" = "1" ] && [ -n "$BACKEND_PID" ]; then
    echo ""
    echo "→ 停止临时后端 (pid $BACKEND_PID)"
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

pass() { echo "  ✅ $1"; }
fail() { echo "  ❌ $1"; exit 1; }
section() { echo ""; echo "━━ $1 ━━"; }

wait_for_api() {
  for i in $(seq 1 30); do
    if curl -sf "$API_BASE/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

section "0. 检查 / 启动后端"
echo "  DATABASE_PATH=$DATABASE_PATH"
echo "  POETRY_CHROMA_PATH=$POETRY_CHROMA_PATH"
echo "  PG=$PG_HOST:$PG_PORT/$PG_DATABASE"
[ -f "$DATABASE_PATH" ] || fail "数据库不存在: $DATABASE_PATH"
[ -d "$POETRY_CHROMA_PATH" ] || fail "诗词向量库不存在: $POETRY_CHROMA_PATH"

if curl -sf "$API_BASE/health" >/dev/null 2>&1; then
  pass "后端已在运行: $API_BASE"
else
  echo "→ 启动本地后端..."
  cd "$ROOT/backend"
  if [ -d venv ]; then source venv/bin/activate; fi
  export FLASK_PORT="${FLASK_PORT:-5200}"
  export JWT_SECRET=rehearsal-local-jwt-secret-32bytes!!
  export WECHAT_DEV_MODE=true
  export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-skip}"
  mkdir -p "$(dirname "$DATABASE_PATH")"
  python3 run.py >/tmp/looma-rehearsal.log 2>&1 &
  BACKEND_PID=$!
  STARTED_BACKEND=1
  wait_for_api || fail "后端启动超时，见 /tmp/looma-rehearsal.log"
  pass "后端已启动 (pid $BACKEND_PID)"
fi

section "1. 最小闭环 API"
API_BASE="$API_BASE" "$ROOT/scripts/verify-closed-loop.sh" || fail "闭环烟雾测试失败"
pass "闭环 API 通过"

section "2. 数据持久化（人格 detail + reload）"
TS=$(date +%s)
EMAIL="persist-${TS}@rehearsal.local"
PASS="rehearsal-pass-123"

REG=$(curl -sf -X POST "$API_BASE/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"name\":\"PersistTest\"}")
TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

DETAIL='{"name":"星云艺术家","emoji":"🎨","tagline":"test","desc":"持久化测试","traits":["创造力"]}'
curl -sf -X POST "$API_BASE/v1/game/profile-sync" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"personality_type\":\"星云艺术家\",\"personality_detail\":$(python3 -c "import json; print(json.dumps('$DETAIL'))")}" >/dev/null

PROFILE=$(curl -sf -H "Authorization: Bearer $TOKEN" "$API_BASE/v1/game/profile")
echo "$PROFILE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
detail = d.get('personality_detail', '')
assert d.get('personality_type') == '星云艺术家', d
assert '星云艺术家' in detail or 'emoji' in detail, detail
missions = d.get('missions_completed', [])
assert isinstance(missions, list), missions
print('  personality_type:', d.get('personality_type'))
print('  detail_len:', len(str(detail)))
print('  missions:', missions)
" || fail "持久化校验失败"
pass "人格 detail 落库并可读"

section "3. RAG / 意图置信度"

STATS=$(curl -sf "$API_BASE/v1/poetry/stats" 2>/dev/null || echo '{}')
echo "$STATS" | python3 -c "
import sys, json
d = json.load(sys.stdin)
total = d.get('total') or d.get('count') or sum(v for v in d.values() if isinstance(v, int))
assert total and total > 1000, f'poetry stats too low: {d}'
print(f'  诗词库 total={total}')
" || fail "诗词库 stats 异常（检查 POETRY_CHROMA_PATH）"
pass "诗词向量库可访问"

QUERIES=(
  "推荐一首关于思乡的古诗"
  "帮我匹配适合程序员的岗位"
  "如何写一份好的简历"
)

for Q in "${QUERIES[@]}"; do
  RESP=$(curl -sf -X POST "$API_BASE/v1/ask" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$(python3 -c "import json; print(json.dumps({'query': '''$Q'''}))")")
  echo "$RESP" | python3 -c "
import sys, json, os
d = json.load(sys.stdin)
q = os.environ.get('Q_TEXT', '')
intent = d.get('intent', '?')
conf = d.get('intent_confidence', '?')
sources = d.get('sources') or []
extracted = d.get('extracted')
scores = [s.get('score') for s in sources if isinstance(s, dict)]
score_str = ', '.join(f'{s:.3f}' if isinstance(s, float) else 'n/a' for s in scores[:3]) or 'none'
ans = (d.get('answer') or '')[:60].replace(chr(10), ' ')
ext_hint = ''
if isinstance(extracted, dict):
    ext_hint = (extracted.get('title') or extracted.get('content') or '')[:40]
print(f'  Q: {q[:40]}')
print(f'     intent={intent} conf={conf} sources={len(sources)} scores=[{score_str}]')
print(f'     answer={ans}')
if ext_hint:
    print(f'     extracted={ext_hint}...')
assert intent, 'missing intent'
assert conf is not None, 'missing intent_confidence'
if intent == 'poetry':
    assert isinstance(extracted, dict) and (extracted.get('title') or extracted.get('content')), d
else:
    assert (d.get('answer') or '').strip(), 'empty answer'
" Q_TEXT="$Q"
done
pass "RAG 问答 + intent_confidence 返回正常"

section "4. 前端服务提示"
echo "  PlanetX Web:  cd frontend && pnpm --filter @looma/planetx dev   → :5173"
echo "  T-space SaaS: cd frontend && pnpm --filter @looma/saas dev      → :5174"
echo "  小程序:       微信开发者工具 → packages/miniprogram"
echo "                utils/config.ts → API_BASE=$API_BASE"
echo "                勾选「不校验合法域名」"

section "完成"
echo ""
echo "🎬 本地彩排 API 层全部通过"
echo "   下一步：启动 :5173/:5174，浏览器 + 小程序走一遍闭环演示"
