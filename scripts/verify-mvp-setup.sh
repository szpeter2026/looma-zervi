#!/bin/bash
# ============================================================================
# verify-mvp-setup.sh — 验证MVP联调环境设置
# 快速检查所有必需组件是否就绪
# ============================================================================

set -e

echo "🔍 MVP联调环境验证"
echo "=========================================================="

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}✅ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# 检查目录
ROOT_DIR=$(pwd)
if [ ! -f "$ROOT_DIR/pyproject.toml" ]; then
    echo "请在仓库根目录运行（需包含 pyproject.toml、backend/、frontend/）"
    exit 1
fi

echo "项目根目录: $ROOT_DIR"
echo ""

# 1. 检查依赖
echo "1. 依赖检查:"
if command -v node &> /dev/null; then
    pass "Node.js $(node --version)"
else
    fail "Node.js 未安装"
fi

if command -v pnpm &> /dev/null; then
    pass "pnpm $(pnpm --version)"
else
    fail "pnpm 未安装"
fi

if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version | awk '{print $2}')
    if [[ "$PY_VERSION" > "3.10" ]]; then
        pass "Python $PY_VERSION"
    else
        warn "Python $PY_VERSION (需要 3.10+)"
    fi
else
    fail "Python 3 未安装"
fi

if command -v docker &> /dev/null; then
    pass "Docker $(docker --version | awk '{print $3}' | tr -d ',')"
else
    warn "Docker 未安装 (ChromaDB将使用本地文件模式)"
fi

echo ""

# 2. 检查后端
echo "2. 后端检查:"
if [ -d "$ROOT_DIR/backend/venv" ]; then
    BACKEND_PY="$ROOT_DIR/backend/venv/bin/python"
    if [ -f "$BACKEND_PY" ]; then
        BACKEND_VERSION=$("$BACKEND_PY" --version 2>&1 | awk '{print $2}')
        pass "Python虚拟环境 $BACKEND_VERSION"
    else
        fail "后端虚拟环境不完整"
    fi
else
    warn "后端虚拟环境不存在 (运行: cd backend && ./dev.sh)"
fi

if [ -f "$ROOT_DIR/backend/.env" ]; then
    pass "后端环境配置文件存在"
else
    warn "backend/.env 不存在 (cp .env.example backend/.env 或运行 ./scripts/start-full-mvp.sh)"
fi

if [ -f "$ROOT_DIR/backend/requirements.txt" ]; then
    pass "后端依赖文件存在"
else
    fail "后端 requirements.txt 不存在"
fi

echo ""

# 3. 检查前端
echo "3. 前端检查:"
if [ -d "$ROOT_DIR/frontend/node_modules" ]; then
    pass "前端 node_modules 存在"
else
    warn "前端依赖未安装 (运行: cd frontend && pnpm install)"
fi

if [ -f "$ROOT_DIR/frontend/pnpm-workspace.yaml" ]; then
    pass "pnpm workspace 配置存在"
else
    fail "pnpm workspace 配置不存在"
fi

# 检查各包
for PACKAGE in planetx saas shared-core miniprogram; do
    if [ -d "$ROOT_DIR/frontend/packages/$PACKAGE" ]; then
        pass "$PACKAGE 包存在"
    else
        fail "$PACKAGE 包不存在"
    fi
done

echo ""

# 4. 检查小程序配置
echo "4. 小程序检查:"
MINIPROGRAM_CONFIG="$ROOT_DIR/frontend/packages/miniprogram/utils/config.ts"
if [ -f "$MINIPROGRAM_CONFIG" ]; then
    if grep -q "http://127.0.0.1:5200" "$MINIPROGRAM_CONFIG"; then
        pass "小程序配置指向本地后端"
    else
        warn "小程序配置未指向本地后端"
        echo "  当前: $(grep -i "API_BASE" "$MINIPROGRAM_CONFIG" | head -1)"
        echo "  建议: export const API_BASE = 'http://127.0.0.1:5200'"
    fi
else
    warn "小程序配置文件不存在"
fi

echo ""

# 5. 检查数据目录
echo "5. 数据目录检查:"
if [ -d "$ROOT_DIR/data" ]; then
    pass "数据目录存在"
else
    warn "数据目录不存在 (某些功能可能受限)"
fi

POETRY_CHROMA="$ROOT_DIR/data/poetry_full"
if [ -d "$POETRY_CHROMA" ] && [ -n "$(find "$POETRY_CHROMA" -mindepth 1 -print -quit 2>/dev/null)" ]; then
    pass "诗词向量库存在且有数据"
else
    warn "诗词向量库不存在或为空 (RAG/诗词 Ask 将降级)"
    echo "  路径: $POETRY_CHROMA"
    echo "  导入: cd backend && python scripts/import_poetry.py"
fi

echo ""

# 6. 检查脚本
echo "6. 工具脚本检查:"
SCRIPTS=(
    "scripts/start-full-mvp.sh"
    "scripts/start-miniprogram-local.sh"
    "scripts/verify-p0-local.sh"
    "scripts/rehearsal-local.sh"
    "backend/dev.sh"
)

for SCRIPT in "${SCRIPTS[@]}"; do
    if [ -f "$ROOT_DIR/$SCRIPT" ]; then
        if [ -x "$ROOT_DIR/$SCRIPT" ]; then
            pass "$SCRIPT (可执行)"
        else
            warn "$SCRIPT (需要执行权限)"
        fi
    else
        fail "$SCRIPT 不存在"
    fi
done

echo ""

# 总结
echo "=========================================================="
echo "📋 验证总结:"
echo ""
echo "启动完整环境:"
echo "  ./scripts/start-full-mvp.sh"
echo ""
echo "启动后端:"
echo "  cd backend && ./dev.sh"
echo ""
echo "启动前端Web:"
echo "  cd frontend && pnpm --filter @looma/planetx dev"
echo "  cd frontend && pnpm --filter @looma/saas dev"
echo ""
echo "小程序联调:"
echo "  ./scripts/start-miniprogram-local.sh"
echo ""
echo "API测试:"
echo "  ./scripts/verify-p0-local.sh"
echo "  ./scripts/rehearsal-local.sh"
echo ""
echo "=========================================================="
echo "✅ 验证完成！根据上述建议修复警告项即可开始联调内测。"