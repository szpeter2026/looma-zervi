#!/usr/bin/env bash
#
# sync-remotes.sh — GitHub ↔ Gitee 仓库同步与一致性检测
# 用法:
#   ./scripts/sync-remotes.sh push       # 推送到所有远程仓库
#   ./scripts/sync-remotes.sh check      # 检测所有远程仓库一致性
#   ./scripts/sync-remotes.sh setup      # 初始化/更新远程仓库配置
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/.sync-config.json"
LOG_PREFIX="[sync]"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()   { echo -e "${BLUE}${LOG_PREFIX}${NC} $*"; }
success(){ echo -e "${GREEN}${LOG_PREFIX}${NC} $*"; }
warn()   { echo -e "${YELLOW}${LOG_PREFIX}${NC} $*"; }
error()  { echo -e "${RED}${LOG_PREFIX}${NC} $*"; }

# 读取配置
load_config() {
  if [[ ! -f "$CONFIG_FILE" ]]; then
    error "配置文件不存在: $CONFIG_FILE"
    error "请先编辑 .sync-config.json 填入你的 Gitee 仓库地址"
    exit 1
  fi

  GITHUB_REMOTE=$(jq -r '.remotes.github.name' "$CONFIG_FILE")
  GITHUB_URL=$(jq -r '.remotes.github.url' "$CONFIG_FILE")
  GITEE_REMOTE=$(jq -r '.remotes.gitee.name' "$CONFIG_FILE")
  GITEE_URL=$(jq -r '.remotes.gitee.url' "$CONFIG_FILE")
  BRANCHES=$(jq -r '.branches[]' "$CONFIG_FILE")
  SYNC_TAGS=$(jq -r '.syncTags' "$CONFIG_FILE")

  # 校验 Gitee URL 是否已配置
  if [[ "$GITEE_URL" == *"YOUR_USERNAME"* ]]; then
    warn "============================================"
    warn "  检测到 Gitee URL 尚未配置!"
    warn "  请编辑 .sync-config.json 中的 gitee.url"
    warn "============================================"
  fi
}

# 检测 jq 是否安装
check_prereqs() {
  if ! command -v jq &>/dev/null; then
    error "jq 未安装，请执行: brew install jq"
    exit 1
  fi
}

# 获取远程最新 commit hash
get_remote_hash() {
  local remote="$1"
  local branch="$2"
  git ls-remote "$remote" "refs/heads/$branch" 2>/dev/null | awk '{print $1}'
}

# 获取本地 commit hash
get_local_hash() {
  local branch="$1"
  git rev-parse "$branch" 2>/dev/null
}

# 设置远程仓库
do_setup() {
  info "配置远程仓库..."

  # 确保 GitHub remote 正确
  if git remote get-url "$GITHUB_REMOTE" &>/dev/null; then
    CURRENT_GH=$(git remote get-url "$GITHUB_REMOTE")
    if [[ "$CURRENT_GH" != "$GITHUB_URL" ]]; then
      warn "更新 $GITHUB_REMOTE: $CURRENT_GH -> $GITHUB_URL"
      git remote set-url "$GITHUB_REMOTE" "$GITHUB_URL"
    fi
    success "$GITHUB_REMOTE (GitHub): $GITHUB_URL"
  else
    git remote add "$GITHUB_REMOTE" "$GITHUB_URL"
    success "添加 $GITHUB_REMOTE (GitHub): $GITHUB_URL"
  fi

  # 配置 Gitee
  if git remote get-url "$GITEE_REMOTE" &>/dev/null; then
    CURRENT_GITEE=$(git remote get-url "$GITEE_REMOTE")
    if [[ "$CURRENT_GITEE" != "$GITEE_URL" ]]; then
      warn "更新 $GITEE_REMOTE: $CURRENT_GITEE -> $GITEE_URL"
      git remote set-url "$GITEE_REMOTE" "$GITEE_URL"
    fi
    success "$GITEE_REMOTE (Gitee): $GITEE_URL"
  else
    if [[ "$GITEE_URL" != *"YOUR_USERNAME"* ]]; then
      git remote add "$GITEE_REMOTE" "$GITEE_URL"
      success "添加 $GITEE_REMOTE (Gitee): $GITEE_URL"
    else
      warn "跳过 Gitee: URL 尚未配置"
    fi
  fi

  success "远程仓库配置完成"
  git remote -v
}

# 推送到所有远程
do_push() {
  local force="${1:-}"
  local push_args=""

  if [[ "$force" == "--force" ]]; then
    push_args="--force"
    warn "使用 force push 模式!"
  fi

  info "开始推送..."

  for branch in $BRANCHES; do
    info "推送分支: $branch"

    # 推送到 GitHub
    info "  -> GitHub ($GITHUB_REMOTE)..."
    if git push $push_args "$GITHUB_REMOTE" "$branch"; then
      success "  ✓ GitHub ($branch)"
    else
      error "  ✗ GitHub ($branch) 推送失败"
    fi

    # 推送到 Gitee
    if git remote get-url "$GITEE_REMOTE" &>/dev/null; then
      info "  -> Gitee ($GITEE_REMOTE)..."
      if git push $push_args "$GITEE_REMOTE" "$branch"; then
        success "  ✓ Gitee ($branch)"
      else
        error "  ✗ Gitee ($branch) 推送失败"
      fi
    fi
  done

  # 推送 tags
  if [[ "$SYNC_TAGS" == "true" ]]; then
    info "推送 tags..."

    if git push "$GITHUB_REMOTE" --tags 2>/dev/null; then
      success "  ✓ GitHub tags"
    else
      warn "  ! GitHub tags 推送失败或无 tags"
    fi

    if git remote get-url "$GITEE_REMOTE" &>/dev/null; then
      if git push "$GITEE_REMOTE" --tags 2>/dev/null; then
        success "  ✓ Gitee tags"
      else
        warn "  ! Gitee tags 推送失败或无 tags"
      fi
    fi
  fi

  success "推送完成!"
}

# 一致性检测
do_check() {
  info "============================================"
  info "  仓库一致性检测报告"
  info "============================================"
  echo ""

  local all_synced=true
  local local_hash remote_hash
  local has_gitee=false

  if git remote get-url "$GITEE_REMOTE" &>/dev/null; then
    has_gitee=true
  fi

  git fetch "$GITHUB_REMOTE" --quiet 2>/dev/null || warn "无法 fetch $GITHUB_REMOTE"
  if $has_gitee; then
    git fetch "$GITEE_REMOTE" --quiet 2>/dev/null || warn "无法 fetch $GITEE_REMOTE"
  fi

  for branch in $BRANCHES; do
    echo "--- 分支: $branch ---"

    local_hash=$(get_local_hash "$branch" 2>/dev/null || echo "N/A")
    echo "  本地:        ${local_hash:0:8}"

    # GitHub
    remote_hash=$(get_remote_hash "$GITHUB_REMOTE" "$branch")
    if [[ -z "$remote_hash" ]]; then
      echo -e "  GitHub:      ${RED}未找到远程分支${NC}"
      all_synced=false
    else
      echo "  GitHub:      ${remote_hash:0:8}"
      if [[ "$local_hash" == "$remote_hash" ]]; then
        echo -e "  GitHub同步:  ${GREEN}✓ 一致${NC}"
      else
        echo -e "  GitHub同步:  ${RED}✗ 不同步${NC}"
        all_synced=false
      fi
    fi

    # Gitee
    if $has_gitee; then
      remote_hash=$(get_remote_hash "$GITEE_REMOTE" "$branch")
      if [[ -z "$remote_hash" ]]; then
        echo -e "  Gitee:       ${RED}未找到远程分支${NC}"
        all_synced=false
      else
        echo "  Gitee:       ${remote_hash:0:8}"
        if [[ "$local_hash" == "$remote_hash" ]]; then
          echo -e "  Gitee同步:   ${GREEN}✓ 一致${NC}"
        else
          echo -e "  Gitee同步:   ${RED}✗ 不同步${NC}"
          all_synced=false
        fi
      fi
    fi

    echo ""
  done

  # 比较两个远程之间的一致性
  if $has_gitee; then
    echo "--- 远程仓库互比 ---"
    for branch in $BRANCHES; do
      local gh_hash=$(get_remote_hash "$GITHUB_REMOTE" "$branch")
      local ge_hash=$(get_remote_hash "$GITEE_REMOTE" "$branch")
      echo "  $branch: GitHub=${gh_hash:0:8}  Gitee=${ge_hash:0:8}"
      if [[ "$gh_hash" == "$ge_hash" ]] && [[ -n "$gh_hash" ]]; then
        echo -e "          ${GREEN}✓ 一致${NC}"
      else
        echo -e "          ${YELLOW}⚠ 差异: 需同步${NC}"
        all_synced=false
      fi
    done
  fi

  echo ""
  echo "============================================"
  if $all_synced; then
    success "✅ 所有仓库完全同步!"
  else
    warn "⚠️  仓库存在差异，请运行: npm run sync:push"
  fi
  echo "============================================"
}

# 主入口
main() {
  cd "$PROJECT_DIR"
  check_prereqs
  load_config

  case "${1:-check}" in
    setup)
      do_setup
      ;;
    push|sync)
      do_push "${2:-}"
      ;;
    check|status)
      do_check
      ;;
    force)
      do_push "--force"
      ;;
    *)
      echo "用法: $0 {setup|push|check|force}"
      echo ""
      echo "  setup   初始化/更新远程仓库配置"
      echo "  push    推送本地改动到所有远程"
      echo "  check   检测所有远程一致性"
      echo "  force   强制推送 (谨慎使用)"
      exit 1
      ;;
  esac
}

main "$@"
