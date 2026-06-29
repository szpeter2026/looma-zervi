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
    console.log('[App] onLaunch - PlanetX starting...')
    
    // Restore token from storage
    const token = wx.getStorageSync('looma_token')
    if (token) {
      console.log('[App] Found saved token, restoring session')
      store.set('token', token)
      this.globalData.token = token
      this.loadProfile()
    } else {
      console.log('[App] No saved token, starting WeChat login')
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
    console.log('[App] wechatLogin() called')
    wx.login({
      success: (res) => {
        console.log('[App] wx.login success, code:', res.code ? 'received' : 'MISSING')
        if (!res.code) {
          console.error('[App] wx.login failed: no code')
          eventBus.emit('auth:login', { success: false, error: 'no_code' })
          return
        }

        console.log('[App] Calling authApi.wechatLogin with code...')
        authApi.wechatLogin(res.code).then((data: any) => {
          console.log('[App] auth response:', JSON.stringify(data)?.slice(0, 200))
          if (data && data.access_token) {
            const token = data.access_token
            console.log('[App] Login SUCCESS - token received')
            store.set('token', token)
            store.set('user', data.user)
            this.globalData.token = token
            this.globalData.userInfo = data.user
            wx.setStorageSync('looma_token', token)
            eventBus.emit('auth:login', { success: true, user: data.user })
            // Load full game profile
            this.loadProfile()
          } else {
            console.error('[App] auth failed: no access_token in response')
            eventBus.emit('auth:login', { success: false, error: 'no_token' })
          }
        }).catch((err: any) => {
          console.error('[App] auth network error:', err?.message || err || 'unknown')
          eventBus.emit('auth:login', { success: false, error: err?.message || 'network' })
        })
      },
      fail: (err) => {
        console.error('[App] wx.login error:', JSON.stringify(err))
        eventBus.emit('auth:login', { success: false, error: 'wx_login_failed' })
      },
    })
  },

  /**
   * Load user + game profile from backend.
   */
  loadProfile() {
    const token = store.get('token')
    if (!token) {
      console.warn('[App] loadProfile called but no token')
      return
    }

    console.log('[App] Loading game profile...')

    // Load game profile (XP, level, personality, fleet)
    gameApi.getProfile().then((data: any) => {
      console.log('[App] Game profile loaded:', JSON.stringify(data)?.slice(0, 150))
      store.applyGameProfile(data)
    }).catch((err: any) => {
      console.warn('[App] Game profile error (non-critical):', err?.message || err)
      // If 401, token expired
      if (err.message?.includes('过期') || err.message?.includes('Unauthorized') || err.message?.includes('401')) {
        console.warn('[App] Token expired, re-logging in')
        store.reset()
        wx.removeStorageSync('looma_token')
        this.globalData.token = null
        this.wechatLogin()
      }
    })

    // Also load auth profile for user info
    authApi.profile().then((data: any) => {
      console.log('[App] Auth profile loaded')
      store.set('user', data)
      this.globalData.userInfo = data
    }).catch((err: any) => {
      // Non-critical, game profile is more important
      console.warn('[Auth] Profile fetch failed (non-critical):', err?.message || err)
    })
  },

  /** Get auth header (backward compat for legacy code) */
  getAuthHeader() {
    const token = store.get('token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  },
})
