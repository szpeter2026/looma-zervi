/**
 * PlanetX Miniprogram App
 * WeChat entry point - thin shell that handles openid login
 * and forwards to looma backend for all business logic.
 */

// looma backend API base URL
const API_BASE = "https://api.genz.ltd";

App({
  globalData: {
    token: null,
    userInfo: null,
    apiBase: API_BASE,
  },

  onLaunch() {
    // Check if we have a cached token
    const token = wx.getStorageSync("looma_token");
    if (token) {
      this.globalData.token = token;
      this.fetchProfile();
    } else {
      // Auto-login with WeChat
      this.wechatLogin();
    }
  },

  /**
   * WeChat login flow:
   * 1. wx.login() -> get code
   * 2. POST /v1/auth/wechat { code } -> get looma JWT
   * 3. Cache token for subsequent requests
   */
  wechatLogin() {
    wx.login({
      success: (res) => {
        if (!res.code) {
          console.error("wx.login failed: no code");
          return;
        }

        wx.request({
          url: `${API_BASE}/v1/auth/wechat`,
          method: "POST",
          data: { code: res.code },
          header: { "Content-Type": "application/json" },
          success: (resp: any) => {
            if (resp.statusCode === 200 && resp.data.access_token) {
              const token = resp.data.access_token;
              this.globalData.token = token;
              this.globalData.userInfo = resp.data.user;
              wx.setStorageSync("looma_token", token);
            } else {
              console.error("looma auth failed:", resp.data);
            }
          },
          fail: (err) => {
            console.error("network error:", err);
          },
        });
      },
      fail: (err) => {
        console.error("wx.login error:", err);
      },
    });
  },

  /**
   * Fetch user profile from looma backend.
   */
  fetchProfile() {
    if (!this.globalData.token) return;

    wx.request({
      url: `${API_BASE}/v1/auth/profile`,
      method: "GET",
      header: {
        Authorization: `Bearer ${this.globalData.token}`,
      },
      success: (resp: any) => {
        if (resp.statusCode === 200) {
          this.globalData.userInfo = resp.data;
        } else if (resp.statusCode === 401) {
          // Token expired, re-login
          this.globalData.token = null;
          wx.removeStorageSync("looma_token");
          this.wechatLogin();
        }
      },
    });
  },

  /**
   * Get auth header for API requests.
   */
  getAuthHeader() {
    return this.globalData.token
      ? { Authorization: `Bearer ${this.globalData.token}` }
      : {};
  },
});
