#!/usr/bin/env bash
# verify-closed-loop.sh — 最小闭环 API 烟雾测试（备案前内测用）
# 覆盖: 用户闭环 + 诗词数据(P0-L4) + 诗人列表(P1-L1)
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:5200}"
SEEKER_EMAIL="loop-seeker-$(date +%s)@test.local"
HR_EMAIL="loop-hr-$(date +%s)@test.local"
PASS="loop-test-pass"

echo "==> 0. 健康检查"
curl -sf "$API_BASE/health" || { echo "❌ Health check failed"; exit 1; }
echo "    健康检查通过"

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

# ── P0-L4: 诗词数据验证 ──
echo "==> 8. 诗词统计 (P0-L4)"
STATS=$(curl -sf "$API_BASE/v1/poetry/stats")
echo "    $STATS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('total', 0) > 0, 'poetry db empty'; print(f'    总计 {d[\"total\"]} 首')"

echo "==> 9. 诗词浏览 (P0-L4)"
BROWSE=$(curl -sf "$API_BASE/v1/poetry/browse?page=1&per_page=5")
echo "$BROWSE" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['items']) > 0, 'browse returned 0 items'; print(f'    浏览页 {d[\"page\"]}/{d[\"total\"]} 共 {d[\"per_page\"]} 条')"

echo "==> 10. 诗词随机 (P0-L4)"
RANDOM_RESP=$(curl -sf "$API_BASE/v1/poetry/random?count=1")
echo "$RANDOM_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d.get('results', [])) > 0, 'no random poem'; print(f'    随机 1 首: {d[\"results\"][0][\"title\"]}')"

# ── P1-L1: 诗人列表验证 ──
echo "==> 11. 诗人列表 (P1-L1)"
AUTHORS=$(curl -sf "$API_BASE/v1/poetry/authors?page=1&per_page=5")
echo "$AUTHORS" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d['items']) > 0, 'authors returned 0 items'; print(f'    诗人 {d[\"total\"]} 位，首页 {len(d[\"items\"])} 位')"

echo ""
echo "✅ 全量 API 烟雾测试通过 (含诗词 P0-L4 + 诗人 P1-L1)"
echo "   HR 画像页: {T-space}/candidate/share/$SHARE_CODE"
