#!/bin/bash

# 运行Ask API基线测试并记录结果
set -e

echo "🚀 运行Ask API基线测试..."
echo "=========================================="

# 1. 检查后端是否运行
echo "1. 检查后端服务..."
if ! curl -s http://127.0.0.1:5200/health > /dev/null 2>&1; then
    echo "❌ 后端服务未运行在 :5200"
    echo "请先启动后端: cd backend && ./dev.sh"
    exit 1
fi
echo "✅ 后端服务运行正常"

# 2. 运行并发测试 (nocache)
echo ""
echo "2. 运行并发测试 (nocache, 5并发 × 20请求)..."
cd /Users/jason/Projects/looma-zervi

# 运行Python并发测试
python3 scripts/concurrency_test.py \
    --url http://127.0.0.1:5200/v1/ask \
    --token token-b658c985 \
    --concurrency 5 \
    --requests 20 \
    --ready-url http://127.0.0.1:5200/health

# 3. 创建基线结果文件
echo ""
echo "3. 生成基线测试报告..."
cat > docs/k6_baseline_main.json << 'EOF'
{
  "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "environment": "local",
  "api_endpoint": "http://127.0.0.1:5200/v1/ask",
  "test_config": {
    "concurrency": 5,
    "requests": 20,
    "cache_mode": "nocache",
    "backend": "Flask dev server (single worker)",
    "llm_provider": "DeepSeek"
  },
  "results": {
    "summary": "需要运行实际测试获取数据",
    "recommendations": [
      "内测部署需使用gunicorn ≥4 workers",
      "SaaS需要修改为使用非流式API",
      "考虑添加LLM层缓存（类似LLM分支的llm_cache.py）"
    ]
  },
  "next_steps": [
    "安装k6后运行完整压测: npm install -g k6",
    "运行k6测试: k6 run scripts/k6_ask_test_nocache.js --vus 5 --duration 30s",
    "统一SaaS Ask契约到非流式",
    "内测前部署gunicorn配置"
  ]
}
EOF

echo "✅ 基线测试框架已创建"
echo ""
echo "📊 运行完整k6测试:"
echo "  1. 安装k6: brew install k6 或 npm install -g k6"
echo "  2. 运行测试: k6 run scripts/k6_ask_test_nocache.js --vus 5 --duration 30s"
echo "  3. 查看结果后更新 docs/k6_baseline_main.json"
echo ""
echo "📝 注意: 当前使用的是Python并发测试脚本，k6测试需要额外安装k6工具"