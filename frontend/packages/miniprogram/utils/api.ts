/**
 * API utility for miniprogram.
 * Wraps wx.request with auth header and error handling.
 */

const app = getApp();

interface RequestOptions {
  url: string;
  method?: "GET" | "POST" | "PUT" | "DELETE";
  data?: any;
}

interface ApiResponse<T = any> {
  statusCode: number;
  data: T;
}

export function request<T = any>(options: RequestOptions): Promise<T> {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${app.globalData.apiBase}${options.url}`,
      method: options.method || "GET",
      data: options.data,
      header: {
        "Content-Type": "application/json",
        ...app.getAuthHeader(),
      },
      success: (resp: any) => {
        if (resp.statusCode >= 200 && resp.statusCode < 300) {
          resolve(resp.data);
        } else if (resp.statusCode === 401) {
          // Token expired
          app.globalData.token = null;
          wx.removeStorageSync("looma_token");
          app.wechatLogin();
          reject(new Error("Unauthorized"));
        } else {
          reject(new Error(resp.data?.message || `HTTP ${resp.statusCode}`));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || "Network error"));
      },
    });
  });
}
