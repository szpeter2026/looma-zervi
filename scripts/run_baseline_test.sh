#!/bin/bash

# 运行 Ask API 基线测试并记录结果
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_BASE="${API_BASE:-http://127.0.0.1:5200}"
BACKEND_LABEL="${BACKEND_LABEL:-Flask dev server (single worker)}"
CONCURRENCY="${CONCURRENCY:-5}"
REQUESTS="${REQUESTS:-20}"
RESULTS_FILE="${RESULTS_FILE:-$ROOT/docs/k6_baseline_main.json}"

echo "🚀 运行 Ask API 基线测试..."
echo "=========================================="
echo "后端: $BACKEND_LABEL"
echo "配置: ${CONCURRENCY} 并发 × ${REQUESTS} 请求 (nocache)"

echo ""
echo "1. 检查后端服务..."
if ! curl -sf "$API_BASE/health" > /dev/null 2>&1; then
    echo "❌ 后端服务未运行在 :5200"
    echo "请先启动后端: cd backend && ./dev.sh"
    exit 1
fi
echo "✅ 后端服务运行正常"

echo ""
echo "2. 运行并发测试..."
TMP_JSON="$(mktemp)"
python3 "$ROOT/scripts/concurrency_test.py" \
    --url "$API_BASE/v1/ask" \
    --concurrency "$CONCURRENCY" \
    --requests "$REQUESTS" \
    --ready-url "$API_BASE/health" \
    --json-output "$TMP_JSON"

echo ""
echo "3. 生成基线测试报告..."
python3 - "$TMP_JSON" "$RESULTS_FILE" "$BACKEND_LABEL" "$CONCURRENCY" "$REQUESTS" << 'PYEOF'
import json
import sys
from datetime import datetime, timezone

tmp_path, out_path, backend_label, concurrency, requests = sys.argv[1:6]
with open(tmp_path, encoding="utf-8") as fh:
    results = json.load(fh)

latency = results.get("latency_ms", {})
report = {
    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "environment": "local",
    "api_endpoint": "http://127.0.0.1:5200/v1/ask",
    "status": "tested",
    "test_config": {
        "concurrency": int(concurrency),
        "requests": int(requests),
        "cache_mode": "nocache",
        "backend": backend_label,
        "llm_provider": "DeepSeek",
        "auth_mode": "registered user + ask_rag consent",
    },
    "results": results,
    "slo_targets": {
        "ask_p95_nocache_vu5": "< 8s",
        "ask_p95_cache_hit": "< 500ms",
        "error_rate": "< 5%",
        "concurrent_users": ">= 10",
    },
    "slo_pass": {
        "error_rate": results.get("error_rate", 1) < 0.05,
        "p95_under_8s": latency.get("p95", 999999) < 8000,
    },
    "observations": [
        "Ask API 使用 ask_rag consent 门禁",
        "每次请求使用唯一 query 避免结果缓存",
        f"测试后端: {backend_label}",
    ],
    "next_steps": [
        "内测部署使用 gunicorn 多 worker",
        "安装 k6 后运行完整压测: brew install k6",
        "k6 run scripts/k6_ask_test_nocache.js --vus 5 --duration 30s",
    ],
}

with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2, ensure_ascii=False)
    fh.write("\n")

print(f"✅ 基线报告已写入: {out_path}")
if report["slo_pass"]["error_rate"]:
    print("✅ 错误率 SLO 通过 (< 5%)")
else:
    print("❌ 错误率 SLO 未通过")
if report["slo_pass"]["p95_under_8s"]:
    print("✅ P95 延迟 SLO 通过 (< 8s)")
else:
    p95_s = latency.get("p95", 0) / 1000
    print(f"⚠️  P95 延迟 SLO 未通过: {p95_s:.2f}s")
PYEOF

rm -f "$TMP_JSON"

echo ""
echo "📊 可选: 安装 k6 后运行完整压测"
echo "  brew install k6"
echo "  k6 run scripts/k6_ask_test_nocache.js --vus 5 --duration 30s"
