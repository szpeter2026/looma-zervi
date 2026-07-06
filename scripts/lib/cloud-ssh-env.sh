# cloud-ssh-env.sh — 云内测 SSH 公共配置（source 用，勿直接执行）
#
# 环境变量:
#   CLOUD_HOST=1.14.202.161     云 IP（默认）
#   SSH_USER=ubuntu             登录用户（腾讯云 Ubuntu 镜像通常为 ubuntu）
#   SSH_KEY=/path/to/key.pem    PEM 私钥路径
#   SSH_ALIAS=looma-cloud       若已在 ~/.ssh/config 配置 Host 别名，优先使用
#
# 示例:
#   SSH_KEY=~/Downloads/looma.pem SSH_USER=ubuntu ./scripts/deploy-cloud-internal-test.sh
#   SSH_ALIAS=looma-cloud ./scripts/deploy-cloud-internal-test.sh

CLOUD_HOST="${CLOUD_HOST:-1.14.202.161}"
SSH_USER="${SSH_USER:-ubuntu}"
if [ -z "${SSH_KEY:-}" ] && [ -f "${HOME}/Downloads/looma_key.pem" ]; then
  SSH_KEY="${HOME}/Downloads/looma_key.pem"
fi
DEPLOY_PATH="${DEPLOY_PATH:-/opt/looma-zervi}"

if [ -n "${SSH_ALIAS:-}" ]; then
  SSH_TARGET="${SSH_ALIAS}"
else
  SSH_TARGET="${SSH_USER}@${CLOUD_HOST}"
fi

SSH_BASE_OPTS=(-o ServerAliveInterval=30 -o ConnectTimeout=15)
if [ -n "${SSH_KEY:-}" ]; then
  SSH_KEY="${SSH_KEY/#\~/$HOME}"
  if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH_KEY 文件不存在: $SSH_KEY" >&2
    exit 1
  fi
  chmod 400 "$SSH_KEY" 2>/dev/null || true
  SSH_BASE_OPTS+=(-i "$SSH_KEY" -o IdentitiesOnly=yes)
fi

ssh_cloud() {
  ssh "${SSH_BASE_OPTS[@]}" "$SSH_TARGET" "$@"
}

scp_cloud() {
  scp "${SSH_BASE_OPTS[@]}" "$@"
}

# rsync -e 需要字符串形式
RSYNC_SSH="ssh"
for _opt in "${SSH_BASE_OPTS[@]}"; do
  RSYNC_SSH+=" $(printf '%q' "$_opt")"
done

cloud_ssh_preflight() {
  echo "🔗 SSH 预检 → ${SSH_TARGET}"
  if [ -n "${SSH_KEY:-}" ]; then
    echo "   密钥: ${SSH_KEY}"
  fi
  ssh_cloud "echo ok && uname -srm && python3 --version 2>/dev/null || true"
}
