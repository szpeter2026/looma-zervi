# CloudBase 配置说明

> **内测主路径：** 小程序使用 **Looma Flask API**（`utils/config.ts` → `http://127.0.0.1:5200` 或生产域名），**不依赖** CloudBase 云函数登录。

## cloudbaserc.json

`envId: "REPLACE_WITH_YOUR_CLOUDBASE_ENV_ID"` 为占位符。仅在使用 CloudBase 云函数（如历史 `wechat-login`）时需要：

1. 在 [腾讯云 CloudBase 控制台](https://console.cloud.tencent.com/tcb) 创建环境
2. 将 `envId` 写入 `cloudbaserc.json`
3. 配置 `CLOUDBASE_ENV_ID`（见仓库根 `.env.example`）

**未配置 CloudBase 不影响：** 微信开发者工具 + `WECHAT_DEV_MODE=true` + Looma `/v1/auth/wechat` 本地联调。
