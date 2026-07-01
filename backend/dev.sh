#!/bin/bash
# ============================================================
# dev.sh — looma 后端一键启动脚本
# Usage: cd backend && ./dev.sh
#
# 自动完成以下操作：
# 1. 检测/创建 Python 虚拟环境
# 2. 安装依赖
# 3. 检查 .env 配置文件
# 4. 创建 data/ 目录
# 5. 以开发模式启动 Flask
# ============================================================
set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[dev.sh]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[dev.sh] WARN${NC} $1"; }
log_error() { echo -e "${RED}[dev.sh] ERROR${NC} $1"; }
log_step()  { echo -e "${CYAN}[dev.sh]${NC} $1"; }

# 切换到 backend 目录
cd "$(dirname "$0")"
BACKEND_DIR=$(pwd)
REPO_ROOT="$(cd .. && pwd)"
log_info "工作目录: $BACKEND_DIR"
log_info "仓库根目录: $REPO_ROOT"

# ============================================
# Step 1: 检测 Python
# ============================================
PYTHON=""
for candidate in python3.11 python3.10 python3.9 python3; do
    if command -v "$candidate" &>/dev/null; then
        version=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        major=$("$candidate" -c 'import sys; print(sys.version_info.major)')
        minor=$("$candidate" -c 'import sys; print(sys.version_info.minor)')
        if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
            PYTHON="$candidate"
            log_info "检测到 Python $version ($PYTHON)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    log_error "未找到 Python 3.9+，请安装后再试"
    exit 1
fi

# ============================================
# Step 2: 检测/创建虚拟环境
# ============================================
if [ ! -d "venv" ]; then
    log_step "创建 Python 虚拟环境..."
    $PYTHON -m venv venv
    log_info "虚拟环境创建完成"
    VENV_FRESH=true
else
    log_info "虚拟环境已存在"
    VENV_FRESH=false
fi

# 激活虚拟环境
source venv/bin/activate

# ============================================
# Step 3: 安装依赖
# ============================================
if [ "$VENV_FRESH" = true ] || [ ! -f "venv/.deps_installed" ]; then
    log_step "安装 Python 依赖..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    touch venv/.deps_installed
    log_info "依赖安装完成"
else
    # 即使已安装，也静默检查是否有缺失
    pip install -r requirements.txt -q 2>/dev/null || true
    log_info "依赖已就绪"
fi

# ============================================
# Step 4: 检查 .env 配置文件
# ============================================
if [ ! -f ".env" ]; then
    log_warn ".env 文件不存在，正在创建默认配置..."
    cat > .env << EOF
# looma 后端环境配置（开发用）
# 生产环境请替换为真实值

# Flask
FLASK_ENV=development
FLASK_PORT=5200

# Database
DATABASE_PATH=./data/looma.db

# Poetry ChromaDB（58k 诗词向量，位于仓库根 data/poetry_full）
POETRY_CHROMA_PATH=$REPO_ROOT/data/poetry_full

# pgvector Docker（looma-pgvector，端口 5433）
PG_HOST=127.0.0.1
PG_PORT=5433
PG_USER=jason
PG_PASSWORD=ServBay.dev
PG_DATABASE=looma

# JWT
JWT_SECRET=dev-secret-change-in-production
JWT_EXPIRATION_HOURS=720

# WeChat Mini Program (开发模式跳过 wx.login 验证)
WECHAT_APPID=your_wechat_appid
WECHAT_SECRET=your_wechat_secret
WECHAT_DEV_MODE=true

# AI Model
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# ChromaDB (本地向量数据库)
CHROMA_PERSIST_DIR=./data/chroma

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
EOF
    log_warn "已创建 .env 文件，请根据实际情况修改配置"
    log_warn "  尤其是: DEEPSEEK_API_KEY, WECHAT_APPID, WECHAT_SECRET"
else
    log_info ".env 文件已存在"
fi

# ============================================
# Step 5: 确保 data 目录存在
# ============================================
mkdir -p data
log_info "data/ 目录已就绪"

# ============================================
# Step 6: 环境变量与启动
# ============================================
# 设置开发模式（绕过微信登录验证）
export WECHAT_DEV_MODE=${WECHAT_DEV_MODE:-true}
# Flask 监听端口（需与前端 API 地址一致）
export FLASK_PORT=${FLASK_PORT:-5200}
# 加载 backend/.env，再叠加仓库根 .env（API key / pgvector 等）
if [ -f .env ]; then
  set -a; source .env; set +a
fi
if [ -f "$REPO_ROOT/.env" ]; then
  set -a; source "$REPO_ROOT/.env"; set +a
fi

# 真实数据路径优先（根 .env 里相对路径 ./data/poetry_full 会解析错误）
export DATABASE_PATH="${DATABASE_PATH:-./data/looma.db}"
if [[ "$POETRY_CHROMA_PATH" != /* ]] || [ ! -d "$POETRY_CHROMA_PATH" ]; then
  export POETRY_CHROMA_PATH="$REPO_ROOT/data/poetry_full"
fi
export PG_HOST="${PG_HOST:-127.0.0.1}"
export PG_PORT="${PG_PORT:-5433}"
export PG_USER="${PG_USER:-jason}"
export PG_PASSWORD="${PG_PASSWORD:-ServBay.dev}"
export PG_DATABASE="${PG_DATABASE:-looma}"

if [ ! -d "$POETRY_CHROMA_PATH" ]; then
  log_warn "诗词向量库不存在: $POETRY_CHROMA_PATH（RAG 诗词检索将降级）"
fi

echo ""
log_info "============================================"
log_info "  looma 后端启动中..."
log_info "  WECHAT_DEV_MODE     = $WECHAT_DEV_MODE"
log_info "  FLASK_PORT          = $FLASK_PORT"
log_info "  FLASK_ENV           = ${FLASK_ENV:-development}"
log_info "  DATABASE_PATH       = $DATABASE_PATH"
log_info "  POETRY_CHROMA_PATH  = $POETRY_CHROMA_PATH"
log_info "  PG                  = $PG_HOST:$PG_PORT/$PG_DATABASE"
log_info "  访问地址: http://localhost:${FLASK_PORT:-5200}"
log_info "============================================"
echo ""

# 启动 Flask
exec python run.py
