/**
 * API client for PlanetX miniprogram.
 *
 * Refactored to align with @looma/shared-core aggregated API pattern:
 * - MiniApiClient: wx.request wrapper with same interface as ApiClient
 * - Factory functions per module  (createMiniAuthApi, createMiniGameApi, ...)
 * - Single client instance shared by all modules
 * - Backward-compatible named exports (authApi, gameApi, askApi, quotaApi)
 */

import { eventBus } from './event-bus'
import { store } from './store'
import { API_BASE } from './config'

// ============================================================
// MiniApiClient — wx.request-based transport
// ============================================================

export interface MiniApiClientConfig {
  baseURL: string
  /** Return current auth token (null if unauthenticated) */
  getToken: () => string | null
  /** Called on 401 response */
  onUnauthorized?: () => void
  /** Default request timeout in ms (default: 10000) */
  timeout?: number
}

export class MiniApiClient {
  private baseURL: string
  private getToken: () => string | null
  private onUnauthorized: () => void
  private defaultTimeout: number

  constructor(config: MiniApiClientConfig) {
    this.baseURL = config.baseURL.replace(/\/$/, '')
    this.getToken = config.getToken
    this.onUnauthorized = config.onUnauthorized ?? (() => {})
    this.defaultTimeout = config.timeout ?? 10000
  }

  /**
   * Core request method wrapping wx.request.
   *
   * Automatically attaches Bearer token except when skipAuth=true.
   * On HTTP 401: clears token, resets store, emits auth:expired.
   */
  private request<T = any>(
    method: string,
    url: string,
    data?: any,
    skipAuth = false,
    timeout?: number,
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const header: Record<string, string> = {
        'Content-Type': 'application/json',
      }

      if (!skipAuth) {
        const token = this.getToken()
        if (token) {
          header['Authorization'] = `Bearer ${token}`
        }
      }

      const fullUrl = `${this.baseURL}${url}`
      console.log(`[API] ${method} ${fullUrl}`)

      wx.request({
        url: fullUrl,
        method: method as any,
        data,
        header,
        timeout: timeout ?? this.defaultTimeout,
        success: (resp: any) => {
          if (resp.statusCode >= 200 && resp.statusCode < 300) {
            resolve(resp.data as T)
          } else if (resp.statusCode === 401) {
            store.reset()
            wx.removeStorageSync('looma_token')
            eventBus.emit('auth:expired')
            this.onUnauthorized()
            reject(new Error('登录已过期，请重新登录'))
          } else {
            const msg =
              resp.data?.message || resp.data?.error || `HTTP ${resp.statusCode}`
            console.error(`[API] Error ${resp.statusCode}:`, msg)
            reject(new Error(msg))
          }
        },
        fail: (err) => {
          let errMsg = err.errMsg || '网络错误'
          if (errMsg.includes('timeout')) {
            errMsg = '请求超时，服务器响应过慢'
          } else if (errMsg.includes('fail')) {
            errMsg = `网络连接失败 (${this.baseURL})`
          }
          console.error('[API] Request failed:', errMsg)
          reject(new Error(errMsg))
        },
      })
    })
  }

  /** GET request */
  get<T = any>(url: string, skipAuth = false): Promise<T> {
    return this.request<T>('GET', url, undefined, skipAuth)
  }

  /** POST request.
   * @param skipAuth - if true, omit Authorization header (e.g. login)
   * @param timeout - per-request timeout override
   */
  post<T = any>(
    url: string,
    data?: any,
    skipAuth = false,
    timeout?: number,
  ): Promise<T> {
    return this.request<T>('POST', url, data, skipAuth, timeout)
  }

  /** PUT request */
  put<T = any>(url: string, data?: any): Promise<T> {
    return this.request<T>('PUT', url, data)
  }

  /** DELETE request */
  del<T = any>(url: string): Promise<T> {
    return this.request<T>('DELETE', url)
  }
}

// ============================================================
// Singleton client (shared by all API modules)
// ============================================================

const client = new MiniApiClient({
  baseURL: API_BASE,
  getToken: () => store.get('token'),
  onUnauthorized: () => {
    eventBus.emit('auth:expired')
  },
})

// ============================================================
// Auth API
// ============================================================

export function createMiniAuthApi(c: MiniApiClient) {
  return {
    /** WeChat login: wx.login code → looma JWT */
    wechatLogin(code: string) {
      return c.post('/v1/auth/wechat', { code }, true, 8000)
    },

    /** Get user profile */
    profile() {
      return c.get('/v1/auth/profile')
    },

    /** Bind email to WeChat account */
    bindEmail(code: string, email: string, password: string) {
      return c.post('/v1/auth/bind', { code, email, password })
    },
  }
}

// ============================================================
// Game API
// ============================================================

export function createMiniGameApi(c: MiniApiClient) {
  return {
    /** Get game profile (XP, level, personality, fleet) */
    getProfile() {
      return c.get('/v1/game/profile')
    },

    /** Sync game profile to backend */
    syncProfile(data: Record<string, any>) {
      return c.post('/v1/game/profile-sync', data)
    },

    /** Complete a mission and earn XP */
    completeMission(missionId: string, xpReward = 10) {
      return c.post('/v1/game/mission-complete', {
        mission_id: missionId,
        xp_reward: xpReward,
      })
    },

    /** Create a fleet */
    createFleet() {
      return c.post('/v1/game/fleet/create')
    },

    /** Join a fleet by invite code */
    joinFleet(code: string) {
      return c.post('/v1/game/fleet/join', { invite_code: code.toUpperCase() })
    },

    /** Get my fleet info */
    getMyFleet() {
      return c.get('/v1/game/fleet/mine')
    },
  }
}

// ============================================================
// Chat / Ask API
// ============================================================

export function createMiniChatApi(c: MiniApiClient) {
  return {
    /** Ask a question to AI */
    ask(query: string, sessionHistory?: any[]) {
      return c.post('/v1/ask', {
        query,
        session_history: sessionHistory || [],
      })
    },
  }
}

// ============================================================
// Quota API
// ============================================================

export function createMiniQuotaApi(c: MiniApiClient) {
  return {
    /** Get quota status */
    getQuota() {
      return c.get('/v1/quota')
    },
  }
}

// ============================================================
// Referral API
// ============================================================

export function createMiniReferralApi(c: MiniApiClient) {
  return {
    create(purpose: 'referral' | 'profile_share' = 'referral') {
      return c.post<{ code: string; purpose?: string }>('/v1/referral/create', { purpose })
    },

    use(code: string) {
      return c.post('/v1/referral/use', { code: code.toUpperCase() })
    },

    profileView(code: string) {
      return c.get(`/v1/referral/profile-view/${encodeURIComponent(code)}`, true)
    },
  }
}

export const authApi = createMiniAuthApi(client)
export const gameApi = createMiniGameApi(client)
export const askApi = createMiniChatApi(client)
export const quotaApi = createMiniQuotaApi(client)
export const referralApi = createMiniReferralApi(client)

export { API_BASE }
