/**
 * PlanetX Miniprogram App
 * WeChat entry point - handles openid login and game profile loading.
 * Uses event bus for state propagation (no more setTimeout polling).
 */

import { eventBus } from './utils/event-bus'
import { store } from './utils/store'
import { authApi, gameApi } from './utils/api'

const API_BASE = 'https://api.genz.ltd'

App({
  globalData: {
    token: null as string | null,
    userInfo: null as any,
    apiBase: API_BASE,
  },

  onLaunch() {
    // Restore token from storage
    const token = wx.getStorageSync('looma_token')
    if (token) {
      store.set('token', token)
      this.globalData.token = token
      this.loadProfile()
    } else {
      // Auto-login with WeChat
      this.wechatLogin()
    }
  },

  /**
   * WeChat login flow:
   * 1. wx.login() -> get code
   * 2. POST /v1/auth/wechat { code } -> get looma JWT
   * 3. Cache token + load game profile
   */
  wechatLogin() {
    wx.login({
      success: (res) => {
        if (!res.code) {
          console.error('[App] wx.login failed: no code')
          eventBus.emit('auth:login', { success: false })
          return
        }

        authApi.wechatLogin(res.code).then((data: any) => {
          if (data.access_token) {
            const token = data.access_token
            store.set('token', token)
            store.set('user', data.user)
            this.globalData.token = token
            this.globalData.userInfo = data.user
            wx.setStorageSync('looma_token', token)
            eventBus.emit('auth:login', { success: true, user: data.user })
            // Load full game profile
            this.loadProfile()
          } else {
            console.error('[App] auth failed:', data)
            eventBus.emit('auth:login', { success: false })
          }
        }).catch((err: any) => {
          console.error('[App] auth network error:', err)
          eventBus.emit('auth:login', { success: false, error: err })
        })
      },
      fail: (err) => {
        console.error('[App] wx.login error:', err)
        eventBus.emit('auth:login', { success: false, error: err })
      },
    })
  },

  /**
   * Load user + game profile from backend.
   */
  loadProfile() {
    const token = store.get('token')
    if (!token) return

    // Load game profile (XP, level, personality, fleet)
    gameApi.getProfile().then((data: any) => {
      store.applyGameProfile(data)
    }).catch((err: any) => {
      console.error('[App] game profile error:', err)
      // If 401, token expired
      if (err.message?.includes('过期') || err.message?.includes('Unauthorized')) {
        store.reset()
        wx.removeStorageSync('looma_token')
        this.globalData.token = null
        this.wechatLogin()
      }
    })

    // Also load auth profile for user info
    authApi.profile().then((data: any) => {
      store.set('user', data)
      this.globalData.userInfo = data
    }).catch(() => {
      // Non-critical, game profile is more important
    })
  },

  /** Get auth header (backward compat for legacy code) */
  getAuthHeader() {
    const token = store.get('token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  },
})
