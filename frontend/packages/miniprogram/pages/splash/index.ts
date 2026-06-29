/**
 * Splash Page - entry point
 * Shows logo, handles auto-login, redirects to hub on success.
 */
import { eventBus } from '../../utils/event-bus'
import { store } from '../../utils/store'

Page({
  data: {
    loading: true,
    loginFailed: false,
  },

  _authHandler: null as any,
  _expiredHandler: null as any,

  onLoad() {
    // Listen for auth events
    this._authHandler = (data: any) => {
      if (data.success) {
        // Login succeeded, go to hub
        wx.switchTab({ url: '/pages/hub/index' })
      } else {
        this.setData({ loading: false, loginFailed: true })
      }
    }
    this._expiredHandler = () => {
      this.setData({ loading: false, loginFailed: true })
    }
    eventBus.on('auth:login', this._authHandler)
    eventBus.on('auth:expired', this._expiredHandler)

    // Check if already logged in (token restored from storage)
    const token = store.get('token')
    if (token) {
      // Wait a moment for profile to load, then go to hub
      setTimeout(() => {
        wx.switchTab({ url: '/pages/hub/index' })
      }, 800)
    }
    // If no token, app.ts will auto-trigger wechatLogin,
    // and the auth:login event will fire.
  },

  onUnload() {
    if (this._authHandler) eventBus.off('auth:login', this._authHandler)
    if (this._expiredHandler) eventBus.off('auth:expired', this._expiredHandler)
  },

  handleRetryLogin() {
    this.setData({ loading: true, loginFailed: false })
    const app = getApp() as any
    app.wechatLogin()
  },
})
