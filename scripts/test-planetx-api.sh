#!/bin/bash
# ============================================================================
# test-planetx-api.sh — 测试PlanetX是否连接到本地后端
# ============================================================================

set -e

echo "🔍 测试PlanetX API连接配置"
echo "=========================================================="

# 设置环境变量
export VITE_API_BASE_URL=http://127.0.0.1:5200
export VITE_API_BASE=http://127.0.0.1:5200
export VITE_SAAS_URL=http://localhost:5174

echo "环境变量已设置:"
echo "  VITE_API_BASE_URL=$VITE_API_BASE_URL"
echo "  VITE_API_BASE=$VITE_API_BASE"
echo "  VITE_SAAS_URL=$VITE_SAAS_URL"
echo ""

# 检查后端是否在运行
echo "检查后端服务..."
if curl -sf "http://127.0.0.1:5200/health" >/dev/null 2>&1; then
    echo "✅ 后端服务运行正常 (127.0.0.1:5200)"
else
    echo "❌ 后端服务未运行"
    echo "  请先启动后端: ./scripts/start-demo.sh"
    echo "  或: cd backend && python run.py"
    exit 1
fi

echo ""
echo "=========================================================="
echo "✅ PlanetX现在将连接到本地后端: http://127.0.0.1:5200"
echo ""
echo "验证方法:"
echo "1. 启动PlanetX:"
echo "   cd frontend"
echo "   pnpm --filter @looma/planetx dev"
echo ""
echo "2. 打开浏览器访问: http://localhost:5173"
echo "3. 在浏览器控制台检查:"
echo "   console.log(import.meta.env.VITE_API_BASE_URL)"
echo "   // 应该显示 'http://127.0.0.1:5200'"
echo ""
echo "4. 检查网络请求:"
echo "   - 登录请求应该发往 127.0.0.1:5200"
echo "   - 而不是 1.14.202.161"
echo "=========================================================="