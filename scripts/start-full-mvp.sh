#!/bin/bash
# ============================================================================
# start-full-mvp.sh — 完整的本地MVP联调内测环境启动脚本
# 启动：后端 + 前端Web + 小程序构建链检查 + 数据库服务
# ============================================================================

set -e

echo "🚀 Looma-Zervi 完整MVP联调内测环境启动"
echo "=========================================================="
echo "架构："
echo "  • 后端: Flask (:5200)"
echo "  • 前端Web: PlanetX (:5173) + T-space (:5174)"
echo "  • 小程序: 微信开发者工具"
echo "  • 数据库: SQLite + ChromaDB (:8000)"
echo "=========================================================="

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[MVP]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[MVP] WARN${NC} $1"; }
log_error() { echo -e "${RED}[MVP] ERROR${NC} $1"; }
log_step()  { echo -e "${CYAN}[MVP]${NC} $1"; }

# 检查是否在项目根目录
if [ ! -f "pyproject.toml" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    log_error "请在仓库根目录运行本脚本（需包含 pyproject.toml、backend/、frontend/）"
    exit 1
fi

ROOT_DIR=$(pwd)
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
MINIPROGRAM_DIR="$FRONTEND_DIR/packages/miniprogram"

# 清理函数
cleanup() {
    echo ""
    log_step "清理进程..."
    if [ -n "$BACKEND_PID" ]; then
        log_info "停止后端进程 (pid: $BACKEND_PID)"
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$PLANETX_PID" ]; then
        log_info "停止 PlanetX 前端进程 (pid: $PLANETX_PID)"
        kill "$PLANETX_PID" 2>/dev/null || true
    fi
    if [ -n "$SAAS_PID" ]; then
        log_info "停止 T-space 前端进程 (pid: $SAAS_PID)"
        kill "$SAAS_PID" 2>/dev/null || true
    fi
    log_info "清理完成"
}

trap cleanup EXIT INT TERM

# ============================================
# 步骤1: 环境检查
# ============================================
log_step "1. 环境检查..."

# 检查 Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js 未安装"
    echo "  安装: https://nodejs.org/"
    exit 1
fi

# 检查 pnpm
if ! command -v pnpm &> /dev/null; then
    log_error "pnpm 未安装"
    echo "  安装: npm install -g pnpm"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 未安装"
    echo "  安装: brew install python@3.12 (macOS)"
    exit 1
fi

# 检查 Docker (可选，用于 ChromaDB)
if ! command -v docker &> /dev/null; then
    log_warn "Docker 未安装，ChromaDB 将使用本地文件模式"
    log_warn "如需向量搜索功能，请安装 Docker: https://docs.docker.com/get-docker/"
fi

log_info "环境检查通过"

# ============================================
# 步骤2: 后端环境准备
# ============================================
log_step "2. 后端环境准备..."

cd "$BACKEND_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    log_info "创建 Python 虚拟环境..."
    python3 -m venv venv
    log_info "虚拟环境创建完成"
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.deps_installed" ]; then
    log_info "安装 Python 依赖..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    touch venv/.deps_installed
    log_info "依赖安装完成"
else
    log_info "Python 依赖已就绪"
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    log_warn ".env 文件不存在，从仓库根 .env.example 复制..."
    if [ -f "$ROOT_DIR/.env.example" ]; then
        cp "$ROOT_DIR/.env.example" .env
    elif [ -f ".env.example" ]; then
        cp ".env.example" .env
    else
        log_error "找不到 .env.example，请手动创建 backend/.env"
        exit 1
    fi
    cat >> .env << EOF

# --- start-full-mvp.sh dev overrides ---
WECHAT_DEV_MODE=true
POETRY_CHROMA_PATH=$ROOT_DIR/data/poetry_full
EOF
    log_warn "已创建 backend/.env — 请填写 DEEPSEEK_API_KEY、WECHAT_APPID、WECHAT_APP_SECRET"
else
    log_info ".env 文件已存在"
fi

# 诗词向量库（RAG 必需；缺失时 Ask 会静默降级）
POETRY_DATA="$ROOT_DIR/data/poetry_full"
if [ ! -d "$POETRY_DATA" ] || [ -z "$(find "$POETRY_DATA" -mindepth 1 -print -quit 2>/dev/null)" ]; then
    log_warn "诗词向量库不存在或为空: $POETRY_DATA"
    log_warn "RAG/诗词功能将降级。导入: cd backend && python scripts/import_poetry.py"
    log_warn "详见 docs/LOCAL_MVP_DEBUGGING.md"
fi

# 确保数据目录存在
mkdir -p data "$ROOT_DIR/data"

# 设置开发环境变量
export WECHAT_DEV_MODE=true
export FLASK_PORT=5200

# 设置前端环境变量，确保PlanetX连接到本地后端
export VITE_API_BASE_URL=http://127.0.0.1:5200
export VITE_API_BASE=http://127.0.0.1:5200
export VITE_SAAS_URL=http://localhost:5174

# ============================================
# 步骤3: 启动后端服务
# ============================================
log_step "3. 启动后端服务 (端口: 5200)..."

# 检查后端是否已在运行
if curl -sf "http://localhost:5200/health" >/dev/null 2>&1; then
    log_info "后端服务已在运行"
else
    log_info "启动后端服务..."
    python run.py > /tmp/looma-backend.log 2>&1 &
    BACKEND_PID=$!
    sleep 3
    
    # 等待后端启动
    for i in {1..30}; do
        if curl -sf "http://localhost:5200/health" >/dev/null 2>&1; then
            log_info "后端服务启动成功 (pid: $BACKEND_PID)"
            log_info "日志: /tmp/looma-backend.log"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "后端服务启动超时"
            log_error "请检查日志: /tmp/looma-backend.log"
            exit 1
        fi
        sleep 1
    done
fi

# ============================================
# 步骤4: 前端Web服务
# ============================================
log_step "4. 启动前端Web服务..."

cd "$FRONTEND_DIR"

# 检查前端依赖
if [ ! -d "node_modules" ]; then
    log_info "安装前端依赖..."
    pnpm install
    log_info "前端依赖安装完成"
else
    log_info "前端依赖已就绪"
fi

# 启动 PlanetX (C端)
log_info "启动 PlanetX (端口: 5173)..."
export VITE_API_BASE_URL=http://127.0.0.1:5200
export VITE_API_BASE=http://127.0.0.1:5200
export VITE_SAAS_URL=http://localhost:5174
pnpm --filter @looma/planetx dev > /tmp/planetx.log 2>&1 &
PLANETX_PID=$!
sleep 2

# 启动 T-space (B端)
log_info "启动 T-space (端口: 5174)..."
pnpm --filter @looma/saas dev > /tmp/saas.log 2>&1 &
SAAS_PID=$!
sleep 2

# 检查前端服务
if curl -sf "http://localhost:5173" >/dev/null 2>&1; then
    log_info "PlanetX 前端启动成功 (pid: $PLANETX_PID)"
else
    log_warn "PlanetX 前端启动可能有问题，请检查日志: /tmp/planetx.log"
fi

if curl -sf "http://localhost:5174" >/dev/null 2>&1; then
    log_info "T-space 前端启动成功 (pid: $SAAS_PID)"
else
    log_warn "T-space 前端启动可能有问题，请检查日志: /tmp/saas.log"
fi

# ============================================
# 步骤5: 小程序环境准备
# ============================================
log_step "5. 小程序环境准备..."

cd "$MINIPROGRAM_DIR"

# 检查小程序配置
CONFIG_FILE="utils/config.ts"
if [ -f "$CONFIG_FILE" ]; then
    if grep -q "http://127.0.0.1:5200" "$CONFIG_FILE"; then
        log_info "小程序配置已指向本地后端"
    else
        log_warn "小程序配置未指向本地后端"
        log_info "当前配置: $(grep -i "API_BASE" "$CONFIG_FILE" | head -1)"
        log_info "需要修改为: export const API_BASE = 'http://127.0.0.1:5200'"
    fi
else
    log_error "找不到小程序配置文件: $CONFIG_FILE"
fi

# 检查构建链
log_info "运行小程序构建链检查..."
if node scripts/quick-check.js 2>/dev/null; then
    log_info "小程序构建链检查通过"
else
    log_warn "小程序构建链检查发现问题 — 请运行: cd frontend && pnpm --filter @looma/miniprogram run build:npm"
    log_warn "然后在微信开发者工具: 工具 → 构建 npm → 编译"
fi

# ============================================
# 步骤6: 可选数据库服务 (ChromaDB)
# ============================================
log_step "6. 可选数据库服务 (ChromaDB)..."

# 检查 ChromaDB 是否在运行
if docker ps | grep -q "chromadb"; then
    log_info "ChromaDB 容器已在运行"
elif command -v docker &> /dev/null; then
    log_info "启动 ChromaDB (端口: 8000) [可选扩展向量库]..."
    docker run -d \
        --name looma-chromadb \
        -p 8000:8000 \
        -v chroma-data:/chroma/chroma \
        -e CHROMA_DB_IMPL=duckdb+parquet \
        -e PERSIST_DIRECTORY=/chroma/chroma \
        chromadb/chroma:latest > /tmp/chromadb.log 2>&1
    
    if [ $? -eq 0 ]; then
        log_info "ChromaDB 启动成功"
        log_info "向量数据库地址: http://localhost:8000"
    else
        log_warn "ChromaDB 启动失败，将使用本地文件模式"
    fi
else
    log_info "Docker 未安装，跳过 ChromaDB 容器启动"
    log_info "后端将使用本地文件模式存储向量数据"
fi

# ============================================
# 步骤7: 验证所有服务
# ============================================
log_step "7. 服务验证..."

echo ""
log_info "服务状态:"
echo "  ✅ 后端 API:     http://localhost:5200"
echo "  ✅ PlanetX Web:  http://localhost:5173"
echo "  ✅ T-space Web:  http://localhost:5174"
echo "  ✅ ChromaDB:     http://localhost:8000 (如果已启动)"
echo "  📱 小程序:      微信开发者工具导入: $MINIPROGRAM_DIR"
echo ""

# 验证后端API
log_info "验证后端API..."
if curl -sf "http://localhost:5200/health" >/dev/null 2>&1; then
    log_info "后端API健康检查: 通过"
else
    log_error "后端API健康检查失败"
fi

# ============================================
# 步骤8: 使用说明
# ============================================
log_step "8. 使用说明"

echo ""
echo "🎯 联调内测环境已就绪！"
echo ""
echo "📱 小程序本地联调:"
echo "  1. 打开微信开发者工具"
echo "  2. 导入项目: $MINIPROGRAM_DIR"
echo "  3. 项目设置 → 本地设置:"
echo "     • ☑️ 不校验合法域名"
echo "     • ☑️ 不校验 TLS 版本"
echo "  4. 工具 → 构建 npm"
echo "  5. 测试核心链路:"
echo "     • pages/hub/index (主页面)"
echo "     • pages/ask/index (提问 + Consent: ask_rag)"
echo "     • app.ts / pages/splash (登录: wechatLogin)"
echo "     • pages/result/index (分享 + Consent: profile_share)"
echo ""
echo "🌐 Web端访问:"
echo "  • PlanetX (C端求职者): http://localhost:5173"
echo "  • T-space (B端HR企业): http://localhost:5174"
echo ""
echo "🔧 开发工具:"
echo "  • 后端日志: tail -f /tmp/looma-backend.log"
echo "  • PlanetX日志: tail -f /tmp/planetx.log"
echo "  • T-space日志: tail -f /tmp/saas.log"
echo ""
echo "🧪 测试脚本:"
echo "  # API合规测试"
echo "  bash scripts/verify-p0-local.sh"
echo ""
echo "  # 完整本地彩排"
echo "  bash scripts/rehearsal-local.sh"
echo ""
echo "  # 小程序本地联调"
echo "  bash scripts/start-miniprogram-local.sh"
echo ""
echo "🛑 停止所有服务:"
echo "  按 Ctrl+C 或运行: pkill -f 'python run.py|vite' && docker stop looma-chromadb"
echo ""
echo "=========================================================="
echo "✅ MVP联调内测环境启动完成！"
echo "=========================================================="

# 保持脚本运行，等待用户中断
log_info "按 Ctrl+C 停止所有服务..."
wait