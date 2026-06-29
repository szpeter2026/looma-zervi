/**
 * Index page - entry point for miniprogram.
 * Handles auto-login and displays welcome screen.
 */

Page({
  data: {
    loading: true,
    userInfo: null,
  },

  onLoad() {
    this.checkAuthStatus();
  },

  checkAuthStatus() {
    const app = getApp();
    // Wait a moment for app.onLaunch to complete
    setTimeout(() => {
      if (app.globalData.token && app.globalData.userInfo) {
        this.setData({
          loading: false,
          userInfo: app.globalData.userInfo,
        });
      } else {
        this.setData({ loading: false });
      }
    }, 1500);
  },

  handleLogin() {
    const app = getApp();
    this.setData({ loading: true });

    app.wechatLogin();

    // Poll for token (simplified - in production use event bus)
    setTimeout(() => {
      if (app.globalData.token) {
        this.setData({
          loading: false,
          userInfo: app.globalData.userInfo,
        });
      } else {
        this.setData({ loading: false });
        wx.showToast({ title: "登录失败，请重试", icon: "none" });
      }
    }, 2000);
  },
});
