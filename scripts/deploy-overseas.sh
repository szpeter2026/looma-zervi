#!/usr/bin/env bash
# Overseas VPS deployment script for looma-zervi (release/overseas)
# Target: Ubuntu 22.04 LTS, Vultr Singapore
# Domain: genz.ltd (Cloudflare DNS + proxy)
#
# Run as root:
#   curl -fsSL https://.../deploy.sh | bash
# Or download and execute manually.

set -euo pipefail

DOMAIN="genz.ltd"
API_SUBDOMAIN="api.genz.ltd"
TSPACE_SUBDOMAIN="tspace.genz.ltd"
REPO_URL="https://gitee.com/szbenyx/looma-zervi.git"
BRANCH="release/overseas"
APP_DIR="/opt/looma-zervi"

export DEBIAN_FRONTEND=noninteractive

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

# ============================
# 1. Basic system setup
# ============================
log "Updating system packages..."
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release software-properties-common ufw git

log "Configuring timezone..."
timedatectl set-timezone Asia/Singapore || true

# ============================
# 2. Docker + Docker Compose
# ============================
log "Installing Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" >/etc/apt/sources.list.d/docker.list
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

log "Installing docker-compose (standalone)..."
DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -oP '"tag_name": "\K[^"]+')
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# ============================
# 3. Certbot + Nginx
# ============================
log "Installing Certbot and Nginx..."
apt-get install -y certbot python3-certbot-nginx nginx

# Stop nginx temporarily to free port 80 for certbot standalone
systemctl stop nginx || true

log "Requesting Let's Encrypt certificate for ${DOMAIN} and subdomains..."
certbot certonly --standalone --non-interactive --agree-tos \
    --email "admin@${DOMAIN}" \
    -d "${DOMAIN}" -d "*.${DOMAIN}" \
    --cert-name "${DOMAIN}" || {
        log "ERROR: certbot failed. Make sure DNS A records for ${DOMAIN} and *.${DOMAIN} point to this server."
        exit 1
    }

# Auto-renewal hook
log "Setting up certbot auto-renewal..."
echo "0 2 * * * root certbot renew --quiet --nginx" >/etc/cron.d/certbot-renew

# ============================
# 4. Clone repository
# ============================
log "Cloning repository ${REPO_URL} branch ${BRANCH}..."
if [ -d "${APP_DIR}" ]; then
    log "Directory exists, pulling latest..."
    cd "${APP_DIR}"
    git fetch origin
    git checkout "${BRANCH}"
    git pull origin "${BRANCH}"
else
    git clone -b "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
    cd "${APP_DIR}"
fi

# ============================
# 5. Configure environment
# ============================
log "Configuring environment..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    log "Created backend/.env from example. You MUST edit it with your secrets."
fi

# Set Redis storage for rate limiting (service name inside docker network)
if ! grep -q "RATE_LIMIT_STORAGE_URI=redis://redis:6379/1" backend/.env; then
    sed -i 's|^RATE_LIMIT_STORAGE_URI=.*|RATE_LIMIT_STORAGE_URI=redis://redis:6379/1|' backend/.env
fi

# Set domain defaults if not already configured
if grep -q "your-domain.com" backend/.env; then
    sed -i "s|your-domain.com|${DOMAIN}|g" backend/.env
fi
if grep -q "GOOGLE_REDIRECT_URI=https://your-domain.com" backend/.env; then
    sed -i "s|GOOGLE_REDIRECT_URI=https://your-domain.com/auth/google/callback|GOOGLE_REDIRECT_URI=https://${API_SUBDOMAIN}/v1/auth/google/callback|g" backend/.env
fi
if grep -q "STRIPE_SUCCESS_URL=https://your-domain.com" backend/.env; then
    sed -i "s|STRIPE_SUCCESS_URL=https://your-domain.com/pricing?status=success|STRIPE_SUCCESS_URL=https://${DOMAIN}/pricing?status=success|g" backend/.env
    sed -i "s|STRIPE_CANCEL_URL=https://your-domain.com/pricing?status=cancel|STRIPE_CANCEL_URL=https://${DOMAIN}/pricing?status=cancel|g" backend/.env
fi

# Set CORS origins
if grep -q "CORS_ORIGINS=http://localhost" backend/.env; then
    sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=https://${DOMAIN},https://${TSPACE_SUBDOMAIN},https://${API_SUBDOMAIN}|g" backend/.env
fi

# ============================
# 6. Build and deploy
# ============================
log "Building and starting services..."
cd docker

docker compose down || true
docker compose pull || true
docker compose up -d --build

log "Waiting for backend to start..."
sleep 10
for i in {1..12}; do
    if curl -fsS http://localhost:5200/health >/dev/null 2>&1; then
        log "Backend is healthy."
        break
    fi
    log "Backend not ready yet, retrying... ($i/12)"
    sleep 5
done

# ============================
# 7. Nginx final config + reload
# ============================
log "Installing Nginx config..."
cp "${APP_DIR}/docker/nginx.conf" /etc/nginx/nginx.conf
nginx -t && systemctl restart nginx
systemctl enable nginx

# ============================
# 8. Firewall
# ============================
log "Configuring UFW..."
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# ============================
# 9. Health check
# ============================
log "Running public health checks..."
IP=$(curl -s -4 ifconfig.me || true)
log "Server public IP: ${IP}"
log "Apex domain: https://${DOMAIN}/health"
log "API domain: https://${API_SUBDOMAIN}/health"
log "T-space domain: https://${TSPACE_SUBDOMAIN}"

log "========================================"
log "Deployment complete!"
log "Next steps:"
log "1. Edit backend/.env with your real secrets (OpenAI, Google, Stripe)."
log "2. Restart containers: cd /opt/looma-zervi/docker && docker compose restart"
log "3. Verify DNS: ${DOMAIN} and *.${DOMAIN} should resolve to ${IP}"
log "4. Configure Google OAuth + Stripe webhooks using URLs above."
log "========================================"
