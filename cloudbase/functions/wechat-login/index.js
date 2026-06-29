/**
 * CloudBase Function: wechat-login
 *
 * This is a PASS-THROUGH function for the miniprogram shell.
 * It does NOT handle business logic - it only forwards the
 * wx.login code to the looma backend's /v1/auth/wechat endpoint.
 *
 * The miniprogram client can also call the backend directly,
 * but this function provides a fallback for environments where
 * the backend domain isn't in the miniprogram's request whitelist.
 */

const https = require("https");

const LOOMA_API_BASE = "https://api.genz.ltd";

exports.main = async (event, context) => {
  const { code } = event;

  if (!code) {
    return {
      code: "INVALID_PARAM",
      message: "wx.login code is required",
    };
  }

  try {
    const resp = await fetch(`${LOOMA_API_BASE}/v1/auth/wechat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });

    const data = await resp.json();

    if (resp.status === 200 && data.access_token) {
      return {
        code: "SUCCESS",
        access_token: data.access_token,
        user: data.user,
        expires_in: data.expires_in,
      };
    }

    return {
      code: "AUTH_FAILED",
      message: data.message || "Authentication failed",
    };
  } catch (err) {
    return {
      code: "NETWORK_ERROR",
      message: err.message || "Failed to connect to looma backend",
    };
  }
};
