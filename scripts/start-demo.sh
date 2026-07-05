#!/bin/bash
# ============================================================================
# start-demo.sh — 快速演示启动脚本
# 启动后端 + PlanetX前端，适合快速演示和测试
# ============================================================================

set -e

echo "🚀 Looma-Zervi 快速演示启动"
echo "=========================================================="

# 检查是否在项目根目录
if [ ! -f "pyproject.toml" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 请在项目根目录运行本脚本"
    exit 1
fi

# 清理函数
cleanup() {
    echo ""
    echo "🛑 停止所有服务..."
    pkill -f "python run.py" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    echo "✅ 服务已停止"
}

trap cleanup EXIT INT TERM

# 启动后端
echo "📦 启动后端服务 (:5200)..."
cd backend
if [ ! -d "venv" ]; then
    echo "  创建Python虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q 2>/dev/null || true

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "  创建默认.env配置..."
    cat > .env << EOF
FLASK_ENV=development
FLASK_PORT=5200
DATABASE_PATH=./data/looma.db
POETRY_CHROMA_PATH=../data/poetry_full
WECHAT_DEV_MODE=true
JWT_SECRET=dev-secret-change-in-production
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
EOF
fi

mkdir -p data
export WECHAT_DEV_MODE=true
export FLASK_PORT=5200

# 设置前端环境变量，确保PlanetX连接到本地后端
export VITE_API_BASE_URL=http://127.0.0.1:5200
export VITE_API_BASE=http://127.0.0.1:5200
export VITE_SAAS_URL=http://localhost:5174

python run.py > /tmp/looma-demo-backend.log 2>&1 &
BACKEND_PID=$!
sleep 5

# 检查后端是否启动成功
if curl -sf "http://localhost:5200/health" >/dev/null 2>&1; then
    echo "✅ 后端启动成功 (pid: $BACKEND_PID)"
    echo "   日志: /tmp/looma-demo-backend.log"
else
    echo "❌ 后端启动失败，检查日志: /tmp/looma-demo-backend.log"
    exit 1
fi

# 启动前端
echo ""
echo "🌐 启动 PlanetX 前端 (:5173)..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "  安装前端依赖..."
    pnpm install
fi

export VITE_API_BASE_URL=http://127.0.0.1:5200
export VITE_API_BASE=http://127.0.0.1:5200
export VITE_SAAS_URL=http://localhost:5174
pnpm --filter @looma/planetx dev > /tmp/planetx-demo.log 2>&1 &
FRONTEND_PID=$!
sleep 3

# 检查前端是否启动成功
if curl -sf "http://localhost:5173" >/dev/null 2>&1; then
    echo "✅ PlanetX 前端启动成功 (pid: $FRONTEND_PID)"
    echo "   日志: /tmp/planetx-demo.log"
else
    echo "⚠️  PlanetX 前端启动可能有问题，检查日志: /tmp/planetx-demo.log"
fi

echo ""
echo "=========================================================="
echo "🎉 演示环境启动完成！"
echo ""
echo "🔗 访问地址:"
echo "  • 后端API:     http://localhost:5200"
echo "  • PlanetX前端: http://localhost:5173"
echo "  • 健康检查:    http://localhost:5200/health"
echo ""
echo "📋 测试命令:"
echo "  # API健康检查"
echo "  curl http://localhost:5200/health"
echo ""
echo "  # 用户注册测试"
echo "  curl -X POST http://localhost:5200/v1/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"demo@test.com\",\"password\":\"demo123\",\"name\":\"Demo User\"}'"
echo ""
echo "🛑 按 Ctrl+C 停止所有服务"
echo "=========================================================="

# 保持脚本运行
wait