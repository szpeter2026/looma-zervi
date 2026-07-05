#!/bin/bash
# ============================================================================
# start-miniprogram-local.sh
# 小程序本地联调一键启动脚本
# 集成：后端启动 + 构建链检查 + 开发者工具提示
# ============================================================================

set -e

echo "🚀 小程序本地联调环境启动"
echo "=========================================================="

# 检查必要工具
echo "🔍 检查环境..."
if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm 未安装，请先安装: npm install -g pnpm"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

# 检查目录
if [ ! -d "frontend/packages/miniprogram" ]; then
    echo "❌ 请在项目根目录运行本脚本"
    exit 1
fi

# 1. 检查 config.ts 配置
echo "📋 1. 检查小程序配置..."
CONFIG_FILE="frontend/packages/miniprogram/src/config.ts"
if [ -f "$CONFIG_FILE" ]; then
    if grep -q "http://127.0.0.1:5200" "$CONFIG_FILE"; then
        echo "   ✅ config.ts 已指向本地后端"
    else
        echo "   ⚠️  config.ts 未指向本地后端"
        echo "      当前配置: $(grep -i "api_base" "$CONFIG_FILE" | head -1)"
        echo "      需要修改为: export const API_BASE = 'http://127.0.0.1:5200'"
        echo ""
        echo "      可选修复:"
        echo "      sed -i \"\" \"s|API_BASE.*|export const API_BASE = 'http://127.0.0.1:5200';|\" $CONFIG_FILE"
    fi
else
    echo "   ❌ 找不到 config.ts"
fi

# 2. 启动后端
echo ""
echo "📦 2. 启动后端服务..."
echo "   执行: cd backend && ./dev.sh"
echo ""
echo "   ℹ️  请在新终端中运行以下命令:"
echo "   cd $(pwd)/backend && ./dev.sh"
echo ""
echo "   或直接运行（按 Ctrl+C 停止后端）:"
echo "   (cd backend && ./dev.sh) &"
echo "   BACKEND_PID=$!"
echo "   trap 'kill $BACKEND_PID 2>/dev/null' EXIT"
echo ""

# 3. 检查构建链
echo "🔧 3. 检查构建链..."
cd frontend/packages/miniprogram

echo "   运行构建链检查..."
node scripts/quick-check.js

echo ""
echo "   如果需要重新构建:"
echo "   pnpm run build:npm"

# 4. 开发者工具指引
echo ""
echo "📱 4. 微信开发者工具操作指引:"
echo ""
echo "   A. 打开微信开发者工具"
echo "   B. 导入项目: $(pwd)"
echo "   C. 设置 → 项目设置 → 本地设置:"
echo "      - ☑️ 不校验合法域名"
echo "      - ☑️ 不校验 TLS 版本"
echo "   D. 工具 → 构建 npm"
echo "   E. 测试页面:"
echo "      1. pages/hub/index (主页面)"
echo "      2. pages/ask/index (提问)"
echo "      3. pages/auth/index (登录)"
echo "      4. pages/profile/index (分享/Consent)"
echo ""

# 5. API 验证脚本
echo "🧪 5. 可选 API 验证:"
echo ""
echo "   A. 后端合规验证:"
echo "      cd $(pwd)/../.. && bash scripts/verify-p0-local.sh"
echo ""
echo "   B. 完整本地彩排:"
echo "      cd $(pwd)/../.. && bash scripts/rehearsal-local.sh"
echo ""

# 6. 快速验证命令
echo "⚡ 6. 快速验证命令汇总:"
echo ""
echo "   # 构建链检查"
echo "   node scripts/quick-check.js"
echo ""
echo "   # 重新构建 npm"
echo "   pnpm run build:npm"
echo ""
echo "   # API 层验证"
echo "   cd ../../.. && bash scripts/verify-p0-local.sh"
echo ""
echo "   # Web E2E 测试（参考）"
echo "   cd frontend && pnpm e2e:live"
echo ""

echo "=========================================================="
echo "✅ 环境准备完成！"
echo ""
echo "下一步:"
echo "1. 在新终端中启动后端: cd backend && ./dev.sh"
echo "2. 确保 config.ts 指向 http://127.0.0.1:5200"
echo "3. 微信开发者工具中导入并构建 npm"
echo "4. 手动点验四条核心链路"
echo ""
echo "📌 注意: Playwright E2E 不覆盖小程序，需要手动测试"
echo "=========================================================="