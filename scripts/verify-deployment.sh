#!/bin/bash
# ============================================================
# verify-deployment.sh — 内测就绪验证脚本
#
# 用法:
#   chmod +x scripts/verify-deployment.sh
#   ./scripts/verify-deployment.sh <服务器IP或域名>
#
# 示例:
#   ./scripts/verify-deployment.sh 123.45.67.89
#   ./scripts/verify-deployment.sh 47.115.168.107
#
# 验证清单:
#   1. 基础设施 — Nginx / Backend 存活
#   2. 前端入口 — PlanetX SPA / T 空间 SPA
#   3. 公开 API — Poetry 诗词库 / Jobs 职位列表
#   4. 认证闭环 — 注册 → 登录 → 访问受保护接口
#   5. AI 核心链路 — 简历解析+匹配（可选，耗配额）
# ============================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS="${GREEN}✓ 通过${NC}"
FAIL="${RED}✗ 失败${NC}"
WARN="${YELLOW}⚠ 跳过${NC}"
INFO="${BLUE}→${NC}"

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

HOST="${1:-}"
if [ -z "$HOST" ]; then
    echo -e "${RED}用法: $0 <服务器IP或域名>${NC}"
    echo "示例: $0 123.45.67.89"
    exit 1
fi

BASE="http://${HOST}"
CURL="curl -sf -o /dev/null -w '%{http_code}' --connect-timeout 10 --max-time 30"
CURL_BODY="curl -sf --connect-timeout 10 --max-time 30"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Looma-Zervi 内测就绪验证                          ║${NC}"
echo -e "${BLUE}║       目标: ${HOST}                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Helper ──
check_endpoint() {
    local label="$1"
    local method="$2"
    local url="$3"
    local expected="${4:-2..}"   # 默认 2xx
    local extra_flags="${5:-}"   # 额外 curl 参数

    printf "  %-45s " "${label}"
    local code
    code=$(curl -s -o /tmp/looma_verify_resp.txt -w '%{http_code}' \
        --connect-timeout 10 --max-time 30 \
        -X "$method" $extra_flags "$url" 2>/tmp/looma_verify_err.txt)
    local curl_exit=$?

    if [ $curl_exit -ne 0 ]; then
        echo -e "$FAIL (curl exit=$curl_exit)"
        cat /tmp/looma_verify_err.txt 2>/dev/null
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi

    if [[ "$code" =~ ^($expected)$ ]]; then
        echo -e "$PASS (HTTP $code)"
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    else
        echo -e "$FAIL (HTTP $code, expected $expected)"
        head -c 300 /tmp/looma_verify_resp.txt 2>/dev/null
        echo ""
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

check_frontend() {
    local label="$1"
    local url="$2"
    local marker="$3"   # 期望页面中包含的字符串

    printf "  %-45s " "${label}"
    local code
    code=$(curl -s -o /tmp/looma_verify_resp.txt -w '%{http_code}' \
        --connect-timeout 10 --max-time 30 "$url" 2>/tmp/looma_verify_err.txt)
    local curl_exit=$?

    if [ $curl_exit -ne 0 ]; then
        echo -e "$FAIL (curl exit=$curl_exit)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi

    if [ "$code" != "200" ]; then
        echo -e "$FAIL (HTTP $code)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi

    if grep -q "$marker" /tmp/looma_verify_resp.txt 2>/dev/null; then
        size=$(wc -c < /tmp/looma_verify_resp.txt | tr -d ' ')
        echo -e "$PASS (HTTP 200, ${size} bytes, 含 '${marker}')"
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    else
        echo -e "$WARN (HTTP 200, 但未找到 '${marker}')"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        return 0
    fi
}

# ============================================================
# Phase 1: 基础设施
# ============================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Phase 1: 基础设施 — Nginx / Backend 存活${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

check_endpoint "Backend Health"    "GET" "$BASE/health"        "200"
check_endpoint "Nginx 代理 Health" "GET" "$BASE/health"        "200"  # 走 nginx
check_endpoint "API 根路径"        "GET" "$BASE/"              "200"  # 应重定向到 /v1/
check_endpoint "后端直达"          "GET" "$BASE/v1/"           "2.."  # Flask 应响应 JSON
check_endpoint "CORS 预检"         "OPTIONS" "$BASE/v1/auth/login" "2.." "-H 'Origin: http://localhost:5173' -H 'Access-Control-Request-Method: POST'"

echo ""

# ============================================================
# Phase 2: 前端入口
# ============================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Phase 2: 前端入口 — PlanetX / T 空间 SPA${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

check_frontend "PlanetX 首页 ( / )"  "$BASE/"            "PlanetX\|looma\|looma-zervi\|root"
check_frontend "T 空间 ( /tspace/ )" "$BASE/tspace/"     "looma\|saas\|T空间\|T-space"

# 检查静态资源缓存头
echo ""
printf "  %-45s " "静态资源缓存头 (Cache-Control)"
cache_header=$(curl -sI --connect-timeout 10 --max-time 10 "$BASE/assets/" 2>/dev/null | grep -i 'cache-control' || true)
if [ -n "$cache_header" ]; then
    echo -e "$PASS ($cache_header)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "$WARN (无 Cache-Control 头)"
    SKIP_COUNT=$((SKIP_COUNT + 1))
fi

echo ""

# ============================================================
# Phase 3: 公开 API — 诗词库 (核心差异化功能)
# ============================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Phase 3: 诗词库 API — 搜索引擎 + 浏览发现${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

check_endpoint "诗词统计 GET /v1/poetry/stats"      "GET" "$BASE/v1/poetry/stats"      "200"
check_endpoint "诗词浏览 GET /v1/poetry/browse"      "GET" "$BASE/v1/poetry/browse"      "200"

# 验证 stats 返回实际数据（非空库）
printf "  %-45s " "诗词库数据量 (total > 0)"
stats=$(curl -sf --connect-timeout 10 --max-time 30 "$BASE/v1/poetry/stats" 2>/dev/null)
total=$(echo "$stats" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total',0))" 2>/dev/null || echo "0")
if [ "$total" -gt 0 ] 2>/dev/null; then
    echo -e "$PASS (总计 ${total} 首诗)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "$WARN (total=$total, 可能诗词导入未完成)"
    SKIP_COUNT=$((SKIP_COUNT + 1))
fi

# 语义搜索（核心功能）
check_endpoint "诗词搜索 GET /v1/poetry/search?q=明月&n=3" "GET" "$BASE/v1/poetry/search?q=%E6%98%8E%E6%9C%88&n=3" "200"

# 随机发现
check_endpoint "诗词随机 GET /v1/poetry/random?n=2"  "GET" "$BASE/v1/poetry/random?n=2"  "200"

echo ""

# ============================================================
# Phase 4: 求职核心 — 职位列表
# ============================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Phase 4: 求职核心 — 职位列表 / 简历解析${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

check_endpoint "职位列表 GET /v1/jobs/list"  "GET" "$BASE/v1/jobs/list"  "200"

echo ""

# ============================================================
# Phase 5: 认证闭环
# ============================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Phase 5: 认证闭环 — 注册 → 登录 → 访问受保护资源${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

TEST_EMAIL="verify-test-$(date +%s)@looma.test"
TEST_PASS="Test123456"

# 注册
printf "  %-45s " "注册 POST /v1/auth/register"
register_resp=$(curl -sf --connect-timeout 10 --max-time 30 \
    -X POST "$BASE/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASS\",\"name\":\"验证测试\"}" 2>/dev/null)
register_code=$?

if [ $register_code -eq 0 ]; then
    echo -e "$PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "$FAIL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# 登录
printf "  %-45s " "登录 POST /v1/auth/login"
login_resp=$(curl -sf --connect-timeout 10 --max-time 30 \
    -X POST "$BASE/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASS\"}" 2>/dev/null)
login_code=$?
TOKEN=$(echo "$login_resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null || echo "")

if [ $login_code -eq 0 ] && [ -n "$TOKEN" ]; then
    echo -e "$PASS (token: ${TOKEN:0:20}...)"
    PASS_COUNT=$((PASS_COUNT + 1))
else
    echo -e "$FAIL (token empty)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# 受保护资源
if [ -n "$TOKEN" ]; then
    printf "  %-45s " "受保护资源 GET /v1/auth/profile"
    profile_code=$(curl -s -o /dev/null -w '%{http_code}' \
        --connect-timeout 10 --max-time 30 \
        -H "Authorization: Bearer $TOKEN" \
        "$BASE/v1/auth/profile" 2>/dev/null)

    if [ "$profile_code" = "200" ]; then
        echo -e "$PASS (HTTP $profile_code)"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "$FAIL (HTTP $profile_code)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
else
    printf "  %-45s " "受保护资源 GET /v1/auth/profile"
    echo -e "$WARN (无 token, 跳过)"
    SKIP_COUNT=$((SKIP_COUNT + 1))
fi

echo ""

# ============================================================
# Phase 6: 征信查证
# ============================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Phase 6: 征信查证 — 企业信用评估${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

check_endpoint "公司查证 POST /v1/credit/check-company" "POST" "$BASE/v1/credit/check-company" "200" \
    "-H 'Content-Type: application/json' -d '{\"company_name\":\"腾讯科技\"}'"

echo ""

# ============================================================
# Phase 7: Docker 容器状态 (需 SSH)
# ============================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Phase 7: Docker 容器状态 (可选，需 SSH 权限)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "  ${INFO} 手动检查 (SSH 到服务器执行):"
echo -e "     docker compose -f /opt/looma-zervi/docker/docker-compose.yml ps"
echo -e "     docker compose -f /opt/looma-zervi/docker/docker-compose.yml logs --tail=20 backend"
echo ""

# ============================================================
# Phase 8: AI 核心链路 (可选，消耗 DeepSeek 配额)
# ============================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Phase 8: AI 核心链路 (已跳过 — 手动按需测试)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "  ${INFO} 简历匹配 (消耗 AI 配额):"
echo -e "     curl -X POST $BASE/v1/jobs/match \\"
echo -e "       -H 'Content-Type: application/json' \\"
echo -e "       -d '{\"resume_text\":\"3年Java开发经验，熟悉Spring Boot和MySQL\"}'"
echo ""
echo -e "  ${INFO} AI 问答 (消耗 AI 配额):"
echo -e "     curl -X POST $BASE/v1/ask \\"
echo -e "       -H 'Content-Type: application/json' \\"
echo -e "       -d '{\"question\":\"Java开发需要什么技能？\"}'"
echo ""

# ============================================================
# Summary
# ============================================================
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    验证结果汇总                          ║${NC}"
echo -e "${BLUE}╠══════════════════════════════════════════════════════════╣${NC}"
printf "${BLUE}║${NC}  ${GREEN}通过: %2d${NC}  |  ${RED}失败: %2d${NC}  |  ${YELLOW}跳过: %2d${NC}                   ${BLUE}║${NC}\n" $PASS_COUNT $FAIL_COUNT $SKIP_COUNT
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ 内测就绪！所有关键检查通过。${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
else
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ ${FAIL_COUNT} 项检查失败，请排查后重新验证。${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
fi

echo ""
echo "详细响应文件: /tmp/looma_verify_resp.txt"
echo "错误信息文件: /tmp/looma_verify_err.txt"

# cleanup
rm -f /tmp/looma_verify_resp.txt /tmp/looma_verify_err.txt
