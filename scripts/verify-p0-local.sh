#!/usr/bin/env bash
# verify-p0-local.sh — P0 合规 + 闭环 API 本地烟雾测试
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:5200}"
PASS="p0-local-test-pass"
SEEKER_EMAIL="p0-seeker-$(date +%s)@test.local"
HR_EMAIL="p0-hr-$(date +%s)@test.local"

echo "==> 0. Health"
curl -sf "$API_BASE/health" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('status')=='ok'"

echo "==> 1. Compliance required scopes"
curl -sf "$API_BASE/v1/compliance/consent/required" | python3 -c "
import sys,json
d=json.load(sys.stdin)
assert 'credit_query' in d.get('available_scopes',[])
assert d.get('details',{}).get('credit_query')
"

echo "==> 2. Register + consent status"
REG=$(curl -sf -X POST "$API_BASE/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$HR_EMAIL\",\"password\":\"$PASS\",\"name\":\"P0HR\"}")
TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

STATUS=$(curl -sf "$API_BASE/v1/compliance/consent/status" \
  -H "Authorization: Bearer $TOKEN")
echo "$STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']['credit_query'] is False"

echo "==> 3. Credit check blocked without consent"
CODE=$(curl -s -o /tmp/p0-credit-deny.json -w '%{http_code}' -X POST "$API_BASE/v1/credit/check-company" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"company_name":"测试科技"}')
test "$CODE" = "403"
python3 -c "import json; d=json.load(open('/tmp/p0-credit-deny.json')); assert d.get('error')=='consent_required'"

echo "==> 4. Grant credit_query consent"
curl -sf -X POST "$API_BASE/v1/compliance/consent/grant" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope":"credit_query"}' >/dev/null

echo "==> 5. Credit check allowed after consent (200 or 422 if no LLM key)"
CODE=$(curl -s -o /tmp/p0-credit-ok.json -w '%{http_code}' -X POST "$API_BASE/v1/credit/check-company" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"company_name":"测试科技"}')
if [ "$CODE" != "200" ] && [ "$CODE" != "422" ]; then
  echo "Unexpected credit response: $CODE"
  cat /tmp/p0-credit-ok.json
  exit 1
fi

echo "==> 6. Closed-loop smoke (seeker → share → HR import)"
bash "$(dirname "$0")/verify-closed-loop.sh"

echo ""
echo "✅ P0 本地烟雾测试通过 (API: $API_BASE)"
