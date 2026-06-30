#!/bin/bash
# ============================================================
# sync_poetry.sh — 首次手动部署诗词库数据到服务器
#
# Usage:
#   ./scripts/sync_poetry.sh                          # 交互式提示
#   ./scripts/sync_poetry.sh --host 1.2.3.4 --user ubuntu --path /home/ubuntu/looma-zervi
#
# 功能：
# 1. 将本地 data/poetry_full/ (ChromaDB 嵌入式数据) 同步到服务器
# 2. 将数据注入 Docker 命名卷
# 3. 在 backend 容器内运行 import_poetry.py 填充 SQLite poems 表
#
# 前提条件：
#   - 服务器上 Docker + docker compose 已安装
#   - backend 容器已在运行（或至少 docker-compose.yml 存在）
# ============================================================
set -e

# 颜色
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log_info()  { echo -e "${GREEN}[sync]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[sync]${NC} $1"; }
log_error() { echo -e "${RED}[sync]${NC} $1"; }
log_step()  { echo -e "${CYAN}[sync]${NC} $1"; }

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
log_info "项目根目录: $PROJECT_ROOT"

# ── 参数解析 ──
HOST=""
USER="ubuntu"
DEPLOY_PATH=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --host) HOST="$2"; shift 2 ;;
    --user) USER="$2"; shift 2 ;;
    --path) DEPLOY_PATH="$2"; shift 2 ;;
    *) log_error "未知参数: $1"; exit 1 ;;
  esac
done

# 交互式收集缺失参数
if [ -z "$HOST" ]; then
  read -p "服务器 IP / 域名: " HOST
fi
if [ -z "$DEPLOY_PATH" ]; then
  read -p "服务器项目路径 [默认: /home/${USER}/looma-zervi]: " DEPLOY_PATH
  DEPLOY_PATH="${DEPLOY_PATH:-/home/${USER}/looma-zervi}"
fi

# ── 检查本地数据 ──
LOCAL_POETRY="${PROJECT_ROOT}/data/poetry_full"
if [ ! -d "$LOCAL_POETRY" ]; then
  log_error "本地未找到 data/poetry_full/ 目录"
  log_error "请确认已在内网构建好诗词向量数据库后重试"
  exit 1
fi
log_info "本地诗词数据: ${LOCAL_POETRY} ($(du -sh "$LOCAL_POETRY" | cut -f1))"

# ============================================
# Step 1: 同步数据到服务器文件系统
# ============================================
log_step "Step 1/3: 同步诗词数据到服务器..."
ssh "${USER}@${HOST}" "mkdir -p ${DEPLOY_PATH}/data/poetry_full"
rsync -avz --progress \
  "${LOCAL_POETRY}/" \
  "${USER}@${HOST}:${DEPLOY_PATH}/data/poetry_full/"
log_info "数据同步完成"

# ============================================
# Step 2: 注入 Docker 命名卷
# ============================================
log_step "Step 2/3: 注入 Docker 命名卷..."

VOLUME_NAME="looma-zervi_poetry-data"

ssh "${USER}@${HOST}" 'bash -s' << POETRY_VOLUME
set -e
VOLUME_NAME="${VOLUME_NAME}"
DEPLOY_PATH="${DEPLOY_PATH}"

# Check if volume exists
if ! docker volume ls --format '{{.Name}}' | grep -q "^${VOLUME_NAME}\$"; then
  echo "Volume ${VOLUME_NAME} 不存在，请先运行 docker compose up -d 创建"
  exit 1
fi

# Check if already populated
if docker run --rm -v ${VOLUME_NAME}:/data alpine test -f /data/chroma.sqlite3 2>/dev/null; then
  echo "Volume 已有数据，跳过注入"
  exit 0
fi

echo "注入数据到 Docker 卷 ${VOLUME_NAME}..."
docker run --rm \
  -v ${VOLUME_NAME}:/dest \
  -v ${DEPLOY_PATH}/data/poetry_full:/src:ro \
  alpine cp -a /src/. /dest/
echo "注入完成"
POETRY_VOLUME
log_info "Docker 卷注入完成"

# ============================================
# Step 3: 导入到 SQLite
# ============================================
log_step "Step 3/3: 导入诗词到 SQLite poems 表..."

ssh "${USER}@${HOST}" 'bash -s' << POETRY_IMPORT
set -e
DEPLOY_PATH="${DEPLOY_PATH}"

# Check if poems table already has data
COUNT=\$(docker compose -f ${DEPLOY_PATH}/docker/docker-compose.yml exec -T backend \
  python -c "
from src.db.manager import DatabaseManager
db = DatabaseManager('/app/data/looma.db')
db.init_schema()
print(db.get_poetry_stats()['total'])
" 2>/dev/null || echo "0")

if [ "\$COUNT" -gt 0 ] 2>/dev/null; then
  echo "poems 表已有 \${COUNT} 首诗词，跳过导入"
  exit 0
fi

echo "运行 poetry import (ChromaDB → SQLite)..."
docker compose -f ${DEPLOY_PATH}/docker/docker-compose.yml exec -T backend \
  python scripts/import_poetry.py \
    --source-dir /app/poetry_data \
    --db-path /app/data/looma.db \
    --batch-size 500
echo "SQLite 导入完成"
POETRY_IMPORT
log_info "SQLite 导入完成"

# ============================================
echo ""
log_info "============================================"
log_info "  诗词库部署完成！"
log_info "  验证: curl ${HOST}/v1/poetry/search?q=月"
log_info "============================================"
