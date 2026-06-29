/**
 * WeChat Miniprogram API Type Definitions
 * Minimal type declarations for wx global API.
 */

interface IAppOption {
  globalData: {
    token: string | null
    userInfo: any
    apiBase: string
  }
  wechatLogin(): void
  loadProfile(): void
  getAuthHeader(): Record<string, string>
}

declare const wx: {
  // App lifecycle
  getStorageSync(key: string): any
  setStorageSync(key: string, data: any): void
  removeStorageSync(key: string): void

  // Login
  login(opts: { success?: (res: { code: string }) => void; fail?: (err: any) => void }): void

  // Network
  request(opts: {
    url: string
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
    data?: any
    header?: Record<string, string>
    timeout?: number
    success?: (res: { statusCode: number; data: any }) => void
    fail?: (err: { errMsg: string }) => void
  }): void

  // Navigation
  switchTab(opts: { url: string }): void
  redirectTo(opts: { url: string }): void
  navigateTo(opts: { url: string }): void
  navigateBack(opts?: { delta?: number }): void
  reLaunch(opts: { url: string }): void

  // UI
  showToast(opts: { title: string; icon?: 'success' | 'none' | 'loading' }): void
  showLoading(opts: { title: string }): void
  hideLoading(): void
  showModal(opts: {
    title?: string
    content?: string
    showCancel?: boolean
    confirmText?: string
    confirmColor?: string
    success?: (res: { confirm: boolean; cancel: boolean }) => void
  }): void
  showShareMenu(opts: {
    withShareTicket?: boolean
    menus?: string[]
  }): void

  // Scroll
  createSelectorQuery(): any
}

declare const App: (opts: any) => void
declare const Page: (opts: any) => void
declare const Component: (opts: any) => void
declare const getApp: () => IAppOption
declare const getCurrentPages: () => any[]
