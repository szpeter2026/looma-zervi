#!/bin/bash

# 切换到 gunicorn 并运行并发验证
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_BASE="${API_BASE:-http://127.0.0.1:5200}"
WORKERS="$(python3 -c "import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)")"
GUNICORN_LOG="/tmp/looma-gunicorn.log"
FLASK_RESULTS="$ROOT/docs/k6_baseline_flask.json"
GUNICORN_RESULTS="$ROOT/docs/k6_baseline_gunicorn.json"

echo "🔧 gunicorn 并发验证"
echo "=========================================="

stop_port_5200() {
    local pids
    pids="$(lsof -t -i :5200 2>/dev/null || true)"
    if [ -n "$pids" ]; then
        echo "停止端口 5200 上的进程: $pids"
        kill $pids 2>/dev/null || true
        sleep 2
        pids="$(lsof -t -i :5200 2>/dev/null || true)"
        if [ -n "$pids" ]; then
            kill -9 $pids 2>/dev/null || true
            sleep 1
        fi
    fi
}

wait_for_health() {
    local deadline=$((SECONDS + 60))
    while [ "$SECONDS" -lt "$deadline" ]; do
        if curl -sf "$API_BASE/health" > /dev/null 2>&1; then
            return 0
        fi
        sleep 2
    done
    echo "❌ gunicorn 未在 60s 内就绪"
    tail -30 "$GUNICORN_LOG" || true
    return 1
}

echo ""
echo "1. 保存 Flask 基线（如后端正在运行）..."
if curl -sf "$API_BASE/health" > /dev/null 2>&1; then
    BACKEND_LABEL="Flask dev server (single worker)" \
        RESULTS_FILE="$FLASK_RESULTS" \
        "$ROOT/scripts/run_baseline_test.sh"
else
    echo "⚠️  Flask 未运行，跳过 Flask 基线"
fi

echo ""
echo "2. 切换到 gunicorn (${WORKERS} workers)..."
stop_port_5200

cd "$ROOT/backend"
if [ -d venv ]; then
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

nohup ./start_gunicorn.sh > "$GUNICORN_LOG" 2>&1 &
GUNICORN_PID=$!
echo "gunicorn PID: $GUNICORN_PID (日志: $GUNICORN_LOG)"

if ! wait_for_health; then
    exit 1
fi
echo "✅ gunicorn 已就绪"

echo ""
echo "3. 运行 gunicorn 并发测试..."
BACKEND_LABEL="gunicorn (${WORKERS} workers)" \
    RESULTS_FILE="$GUNICORN_RESULTS" \
    "$ROOT/scripts/run_baseline_test.sh"

echo ""
echo "4. 合并对比报告..."
python3 - "$FLASK_RESULTS" "$GUNICORN_RESULTS" "$ROOT/docs/k6_baseline_main.json" << 'PYEOF'
import json
import sys
from datetime import datetime, timezone

flask_path, gunicorn_path, out_path = sys.argv[1:4]

def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None

flask = load(flask_path)
gunicorn = load(gunicorn_path)

report = {
    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "environment": "local",
    "api_endpoint": "http://127.0.0.1:5200/v1/ask",
    "status": "tested",
    "test_config": {
        "concurrency": 5,
        "requests": 20,
        "cache_mode": "nocache",
        "auth_mode": "registered user + ask_rag consent",
    },
    "runs": {},
    "slo_targets": {
        "ask_p95_nocache_vu5": "< 8s",
        "error_rate": "< 5%",
        "concurrent_users": ">= 10",
    },
}

if flask:
    report["runs"]["flask_dev"] = flask
if gunicorn:
    report["runs"]["gunicorn"] = gunicorn

if flask and gunicorn:
    f_lat = flask.get("results", {}).get("latency_ms", {})
    g_lat = gunicorn.get("results", {}).get("latency_ms", {})
    report["comparison"] = {
        "throughput_rps": {
            "flask": flask["results"].get("throughput_rps"),
            "gunicorn": gunicorn["results"].get("throughput_rps"),
        },
        "p95_ms": {
            "flask": f_lat.get("p95"),
            "gunicorn": g_lat.get("p95"),
        },
        "error_rate": {
            "flask": flask["results"].get("error_rate"),
            "gunicorn": gunicorn["results"].get("error_rate"),
        },
    }

with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2, ensure_ascii=False)
    fh.write("\n")

print(f"✅ 对比报告已写入: {out_path}")
PYEOF

echo ""
echo "✅ gunicorn 并发验证完成"
echo "   Flask 结果:   $FLASK_RESULTS"
echo "   gunicorn 结果: $GUNICORN_RESULTS"
echo "   合并报告:     $ROOT/docs/k6_baseline_main.json"
echo ""
echo "gunicorn 仍在后台运行 (PID $GUNICORN_PID)"
echo "停止: kill $GUNICORN_PID 或 lsof -t -i :5200 | xargs kill"
