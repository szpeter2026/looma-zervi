/**
 * API client for PlanetX miniprogram.
 * Wraps wx.request with auth header, error handling, and event bus.
 */

import { eventBus } from './event-bus'
import { store } from './store'

const API_BASE = 'https://api.genz.ltd'

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  /** Skip auth header (e.g. for login) */
  noAuth?: boolean
}

export function request<T = any>(options: RequestOptions): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = store.get('token')
    const header: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token && !options.noAuth) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: `${API_BASE}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header,
      success: (resp: any) => {
        if (resp.statusCode >= 200 && resp.statusCode < 300) {
          resolve(resp.data as T)
        } else if (resp.statusCode === 401) {
          // Token expired
          store.reset()
          wx.removeStorageSync('looma_token')
          eventBus.emit('auth:expired')
          reject(new Error('登录已过期，请重新登录'))
        } else {
          const msg = resp.data?.message || resp.data?.error || `HTTP ${resp.statusCode}`
          reject(new Error(msg))
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || '网络错误'))
      },
    })
  })
}

// ============ Auth API ============
export const authApi = {
  /** WeChat login: code -> looma JWT */
  wechatLogin(code: string): Promise<any> {
    return request({
      url: '/v1/auth/wechat',
      method: 'POST',
      data: { code },
      noAuth: true,
    })
  },

  /** Get user profile */
  profile(): Promise<any> {
    return request({ url: '/v1/auth/profile' })
  },

  /** Bind email to WeChat account */
  bindEmail(code: string, email: string, password: string): Promise<any> {
    return request({
      url: '/v1/auth/bind',
      method: 'POST',
      data: { code, email, password },
    })
  },
}

// ============ Game API ============
export const gameApi = {
  /** Get game profile (XP, level, personality, fleet, missions) */
  getProfile(): Promise<any> {
    return request({ url: '/v1/game/profile' })
  },

  /** Sync game profile to backend */
  syncProfile(data: any): Promise<any> {
    return request({
      url: '/v1/game/profile-sync',
      method: 'POST',
      data,
    })
  },

  /** Complete a mission and earn XP */
  completeMission(missionId: string): Promise<any> {
    return request({
      url: '/v1/game/mission-complete',
      method: 'POST',
      data: { mission_id: missionId },
    })
  },

  /** Create a fleet */
  createFleet(): Promise<any> {
    return request({
      url: '/v1/game/fleet/create',
      method: 'POST',
    })
  },

  /** Join a fleet by invite code */
  joinFleet(code: string): Promise<any> {
    return request({
      url: '/v1/game/fleet/join',
      method: 'POST',
      data: { invite_code: code.toUpperCase() },
    })
  },

  /** Get my fleet info */
  getMyFleet(): Promise<any> {
    return request({ url: '/v1/game/fleet/mine' })
  },
}

// ============ Ask API ============
export const askApi = {
  /** Ask a question to AI */
  ask(query: string, sessionHistory?: any[]): Promise<any> {
    return request({
      url: '/v1/ask',
      method: 'POST',
      data: {
        query,
        session_history: sessionHistory || [],
      },
    })
  },
}

// ============ Quota API ============
export const quotaApi = {
  /** Get quota status */
  getQuota(): Promise<any> {
    return request({ url: '/v1/quota' })
  },
}

export { API_BASE }
