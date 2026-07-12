#!/usr/bin/env bash
# Redeploy genz-web static files only (no Docker rebuild).
# Run on overseas VPS as root after git pull on release/overseas.
#
#   cd /opt/looma-zervi && git pull origin release/overseas
#   bash scripts/deploy-genz-web.sh

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/looma-zervi}"
GENZ_WEB_SRC="${APP_DIR}/frontend/packages/genz-web"
GENZ_WEB_DEST="/var/www/genz-web"

if [ ! -d "${GENZ_WEB_SRC}" ]; then
    echo "Missing ${GENZ_WEB_SRC}" >&2
    exit 1
fi

mkdir -p "${GENZ_WEB_DEST}"
rsync -a --delete \
    --exclude README.md \
    --exclude package.json \
    --exclude vercel.json \
    "${GENZ_WEB_SRC}/" "${GENZ_WEB_DEST}/"

nginx -t && systemctl reload nginx

echo "genz-web deployed to ${GENZ_WEB_DEST}"
echo "Verify: curl -sI https://genz.ltd/ | head -1"
