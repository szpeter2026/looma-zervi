/**
 * Miniprogram runtime config.
 * Local rehearsal: API_BASE=http://127.0.0.1:5000 (WeChat devtools: 不校验合法域名)
 * Remote内测: API_BASE=http://1.14.202.161
 */
export const API_BASE = 'http://127.0.0.1:5200'
export const SAAS_BASE = 'http://localhost:5174'

export const MISSION_XP: Record<string, number> = {
  personality: 50,
  share: 30,
  team: 80,
  match: 40,
}
