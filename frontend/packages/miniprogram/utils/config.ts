/**
 * Miniprogram runtime config.
 * 
 * 环境切换说明：
 * - dev:    本地开发环境，后端运行在 :5200
 * - staging: 远程内测环境，后端运行在服务器 IP
 * - prod:    生产环境，备案域名
 * 
 * 本地联调步骤：
 * 1. 切换到 dev 环境：API_BASE = 'http://127.0.0.1:5200'
 * 2. 启动后端：cd backend && ./dev.sh
 * 3. 微信开发者工具：设置 → 不校验合法域名
 * 4. 构建 npm：pnpm run build:npm
 */

// 开发环境（本地联调）
export const API_BASE = 'http://127.0.0.1:5200'
// export const API_BASE = 'http://1.14.202.161'  // staging 环境
// export const API_BASE = 'https://your-domain.com'  // prod 环境

export const SAAS_BASE = 'http://localhost:5174'

export const MISSION_XP: Record<string, number> = {
  personality: 50,
  share: 30,
  team: 80,
  match: 40,
}
