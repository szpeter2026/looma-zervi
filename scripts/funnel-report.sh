#!/usr/bin/env bash
# funnel-report.sh — 内测闭环漏斗报告（读 /v1/analytics/funnel）
set -euo pipefail

API_BASE="${API_BASE:-http://127.0.0.1:5200}"
DAYS="${1:-30}"
EMAIL="${FUNNEL_EMAIL:-}"
PASS="${FUNNEL_PASS:-}"

if [ -z "$EMAIL" ] || [ -z "$PASS" ]; then
  echo "用法: FUNNEL_EMAIL=user@test.local FUNNEL_PASS=secret $0 [days]"
  echo "  （任意已注册个人邮箱；非 HR 专用账号，见 docs/产品介绍与内测说明.md §2）"
  echo "  或: API_BASE=... 且已 export JWT_TOKEN=..."
  exit 1
fi

TOKEN="${JWT_TOKEN:-}"
if [ -z "$TOKEN" ]; then
  TOKEN=$(curl -sf -X POST "$API_BASE/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
fi

echo ""
echo "━━ Looma 内测闭环漏斗（近 ${DAYS} 天）━━"
echo "   API: $API_BASE"
echo ""

curl -sf -H "Authorization: Bearer $TOKEN" "$API_BASE/v1/analytics/funnel?days=$DAYS" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
steps = d.get('steps', {})
conv = d.get('conversion', {})
print('步骤计数:')
for k, v in steps.items():
    print(f'  {k:28} {v}')
print('')
print('逐步转化率:')
for k, v in conv.items():
    pct = f'{v*100:.1f}%' if v is not None else 'n/a'
    print(f'  {k:28} {pct}')
fb = d.get('micro_feedback') or []
if fb:
    print('')
    print('微反馈:')
    for row in fb:
        avg = row.get('avg_score')
        avg_s = f' avg={avg}' if avg is not None else ''
        print(f\"  {row['context']:28} n={row['count']}{avg_s}\")
"

echo ""
echo "详见 docs/内测埋点与闭环漏斗方案.md"
