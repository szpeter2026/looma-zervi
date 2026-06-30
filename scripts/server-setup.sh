#!/bin/bash
# ============================================================
# server-setup.sh — 腾讯云服务器首次环境初始化
#
# 在服务器上执行（以 root 身份）:
#   curl -fsSL https://raw.githubusercontent.com/.../scripts/server-setup.sh | bash
#   或
#   scp scripts/server-setup.sh root@<your-ip>:/tmp/ && ssh root@<your-ip> "bash /tmp/server-setup.sh"
#
# 功能:
#   1. 安装 Docker + Docker Compose
#   2. 创建项目目录结构
#   3. 配置 SSH 密钥（用于 GitHub Actions 部署）
#   4. 创建前端静态文件目录
# ============================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
log()  { echo -e "${GREEN}[setup]${NC} $1"; }
warn() { echo -e "${RED}[setup]${NC} $1"; }

# ============================================
# 1. 安装 Docker
# ============================================
log "安装 Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    log "Docker 安装完成"
else
    log "Docker 已安装: $(docker --version)"
fi

# ============================================
# 2. 安装 Docker Compose (plugin)
# ============================================
log "检查 Docker Compose..."
if ! docker compose version &>/dev/null; then
    warn "未检测到 docker compose plugin，请手动安装"
    warn "参考: https://docs.docker.com/compose/install/linux/"
else
    log "Docker Compose 已就绪"
fi

# ============================================
# 3. 创建项目目录
# ============================================
PROJECT_DIR="/opt/looma-zervi"
log "创建项目目录: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"

# 前端静态文件目录（nginx 挂载）
log "创建前端静态目录..."
mkdir -p /var/www/planetx/dist
mkdir -p /var/www/saas/dist

# Docker 数据卷
mkdir -p "$PROJECT_DIR/docker/certs"

log "目录结构创建完成"
log "  项目代码: $PROJECT_DIR"
log "  PlanetX:  /var/www/planetx/dist"
log "  T-space:  /var/www/saas/dist"
log "  SSL证书:  $PROJECT_DIR/docker/certs"

# ============================================
# 4. 生成部署专用 SSH 密钥（可选）
# ============================================
log "生成部署专用 SSH 密钥..."
SSH_KEY="$HOME/.ssh/github-actions-deploy"
if [ ! -f "$SSH_KEY" ]; then
    ssh-keygen -t ed25519 -C "github-actions-deploy" -f "$SSH_KEY" -N ""
    cat "$SSH_KEY.pub" >> "$HOME/.ssh/authorized_keys"
    log "SSH 密钥已生成"
    echo ""
    warn "============================================"
    warn "请将以下私钥添加到 GitHub Secrets:"
    warn "  Secret Name: SSH_PRIVATE_KEY"
    warn "============================================"
    cat "$SSH_KEY"
    echo ""
    warn "============================================"
else
    log "SSH 密钥已存在: $SSH_KEY"
fi

# ============================================
# 5. 输出后续步骤
# ============================================
echo ""
log "============================================"
log "  服务器初始化完成！"
log "============================================"
echo ""
echo "接下来在 GitHub 仓库配置以下 Secrets:"
echo ""
echo "  SSH_HOST          = $(curl -s ifconfig.me 2>/dev/null || echo '<你的服务器IP>')"
echo "  SSH_USER          = root"
echo "  SSH_PRIVATE_KEY   = 上面输出的私钥内容"
echo "  DEPLOY_PATH       = $PROJECT_DIR"
echo ""
echo "然后在服务器上首次拉取代码:"
echo "  cd $PROJECT_DIR"
echo "  git clone https://github.com/<your-org>/looma-zervi.git ."
echo ""
echo "创建 .env 配置文件（替换为真实值）:"
echo "  cp .env.example backend/.env"
echo "  vim backend/.env"
echo ""
echo "启动服务:"
echo "  docker compose -f docker/docker-compose.yml up -d --build"
echo ""
