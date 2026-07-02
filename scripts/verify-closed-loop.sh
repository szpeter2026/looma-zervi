#!/usr/bin/env bash
# verify-closed-loop.sh — 最小闭环 API 烟雾测试（备案前内测用）
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:5200}"
SEEKER_EMAIL="loop-seeker-$(date +%s)@test.local"
HR_EMAIL="loop-hr-$(date +%s)@test.local"
PASS="loop-test-pass"

echo "==> 1. 注册求职者"
SEEKER_RESP=$(curl -sf -X POST "$API_BASE/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$SEEKER_EMAIL\",\"password\":\"$PASS\",\"name\":\"LoopSeeker\"}")
SEEKER_TOKEN=$(echo "$SEEKER_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "==> 2. 同步人格测试结果"
curl -sf -X POST "$API_BASE/v1/game/profile-sync" \
  -H "Authorization: Bearer $SEEKER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"personality_type":"星云艺术家","personality_detail":"{\"name\":\"星云艺术家\",\"emoji\":\"🎨\",\"tagline\":\"test\",\"desc\":\"test\",\"traits\":[\"创造力\"]}"}'

echo "==> 3. 创建画像分享码"
SHARE_RESP=$(curl -sf -X POST "$API_BASE/v1/referral/create" \
  -H "Authorization: Bearer $SEEKER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"purpose":"profile_share"}')
SHARE_CODE=$(echo "$SHARE_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['code'])")
echo "    分享码: $SHARE_CODE"

echo "==> 4. 公开查看画像"
curl -sf "$API_BASE/v1/referral/profile-view/$SHARE_CODE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('personality_type')"

echo "==> 5. HR 注册并创建企业"
HR_RESP=$(curl -sf -X POST "$API_BASE/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$HR_EMAIL\",\"password\":\"$PASS\",\"name\":\"LoopHR\"}")
HR_TOKEN=$(echo "$HR_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -sf -X POST "$API_BASE/v1/enterprise/create" \
  -H "Authorization: Bearer $HR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"闭环测试企业"}'

echo "==> 6. HR 导入候选人"
curl -sf -X POST "$API_BASE/v1/enterprise/candidates/import-share" \
  -H "Authorization: Bearer $HR_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"share_code\":\"$SHARE_CODE\"}"

echo "==> 7. Stub 升级 Pro 试用"
curl -sf -X POST "$API_BASE/v1/payment/upgrade" \
  -H "Authorization: Bearer $HR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier":"pro"}'

echo ""
echo "✅ 最小闭环 API 烟雾测试通过"
echo "   HR 画像页: {T-space}/candidate/share/$SHARE_CODE"
