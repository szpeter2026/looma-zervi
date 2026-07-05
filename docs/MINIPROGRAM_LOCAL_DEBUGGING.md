# 小程序本地联调指南

## 概述

本文档说明如何在本地环境中联调微信小程序，包括后端 API、构建链配置和测试流程。

## 架构对照

```
┌─────────────────────────────────────────────────────────┐
│  Playwright E2E（现有）                                  │
│  SaaS :5174  +  PlanetX :5173  →  浏览器自动化           │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────┐
│  Flask 后端 :5200  ← dev.sh / e2e-backend.sh            │
│  WECHAT_DEV_MODE=true  →  微信登录可 mock                │
└───────────────────────────▲─────────────────────────────┘
                            │ wx.request
┌───────────────────────────┴─────────────────────────────┐
│  微信小程序  ← 无 Playwright，需开发者工具 / 真机手动点验   │
└─────────────────────────────────────────────────────────┘
```

## 复用组件

### 1. 后端 API ✅ 完全复用
- 同一套 Flask 后端 (:5200)
- `WECHAT_DEV_MODE=true` 启用微信登录 mock
- 相同的 API 端点：
  - `/v1/auth/wechat` - 登录
  - `/v1/ask` - 提问
  - `/v1/referral/create` - 分享
  - `/v1/compliance/consent/*` - Consent

### 2. API 验证脚本 ✅ 完全适用
- `verify-p0-local.sh` - 后端合规验证
- `rehearsal-local.sh` - 完整本地彩排
- 验证的是后端行为，与调用端无关

### 3. Playwright E2E ❌ 不适用
- 只覆盖 SaaS (:5174) 和 PlanetX (:5173)
- 无小程序自动化测试

## 本地联调步骤

### 快速开始
```bash
# 一键启动脚本
bash scripts/start-miniprogram-local.sh
```

### 详细步骤

#### 1. 配置小程序指向本地
修改 `frontend/packages/miniprogram/src/config.ts`：
```typescript
export const API_BASE = 'http://127.0.0.1:5200';
```

#### 2. 启动后端服务
```bash
cd backend && ./dev.sh
```

#### 3. 构建 npm 包
```bash
cd frontend/packages/miniprogram
pnpm run build:npm
```

#### 4. 微信开发者工具操作
1. 打开微信开发者工具
2. 导入项目：`frontend/packages/miniprogram`
3. 设置 → 项目设置 → 本地设置：
   - ☑️ 不校验合法域名
   - ☑️ 不校验 TLS 版本
4. 工具 → 构建 npm
5. 测试页面：
   - `pages/hub/index` - 主页面
   - `pages/ask/index` - 提问
   - `pages/auth/index` - 登录
   - `pages/profile/index` - 分享/Consent

## 验证分工

| 验证项 | 工具 | 覆盖端 | 说明 |
|--------|------|--------|------|
| 后端合规 | `verify-p0-local.sh` | 全端 API | 验证后端接口合规性 |
| Consent 闭环 | `verify-p0-local.sh` | 全端 API | 验证 consent 流程 |
| Web UI 闭环 | `pnpm e2e:live:all` | SaaS + PlanetX | Playwright 自动化测试 |
| 小程序构建链 | `pnpm run build:npm` | 小程序 | 验证 npm 构建 |
| 小程序业务链路 | 微信开发者工具 + 真机 | 小程序 only | 手动点验四条核心链路 |

## 核心链路验证清单

### 1. 登录链路
- [ ] 小程序 `wx.login()` 成功
- [ ] 获取到 mock openid (`dev_*`)
- [ ] 成功换取 JWT token
- [ ] 用户信息正确同步

### 2. Ask 链路
- [ ] 提问页面正常加载
- [ ] 输入问题并提交
- [ ] 成功获取回答
- [ ] 回答显示正常

### 3. 分享链路
- [ ] 生成分享码
- [ ] 分享页面正常
- [ ] 被分享者可通过分享码访问

### 4. Consent 链路
- [ ] 首次访问提示 consent
- [ ] 同意后记录到后端
- [ ] 后续访问不再重复提示

## 调试技巧

### 查看后端日志
```bash
cd backend && tail -f logs/development.log
```

### 快速构建检查
```bash
cd frontend/packages/miniprogram
node scripts/quick-check.js
```

### API 层验证
```bash
# 后端合规验证
bash scripts/verify-p0-local.sh

# 完整本地彩排
bash scripts/rehearsal-local.sh
```

## 常见问题

### Q: 开发者工具提示"不校验合法域名"仍报错？
A: 确保完全关闭开发者工具后重新打开，设置才会生效。

### Q: 构建 npm 失败？
A: 运行 `pnpm run build:npm:clean` 清理后重试。

### Q: 本地后端启动失败？
A: 检查端口 5200 是否被占用：`lsof -i :5200`

### Q: 微信登录 mock 不工作？
A: 确保后端启动时 `WECHAT_DEV_MODE=true`，可在 `dev.sh` 中确认。

## 下一步自动化（P2 规划）

如需将小程序纳入自动化测试，可考虑：
1. 集成 `miniprogram-automator`
2. 创建 `*.mini.live.spec.ts` 测试文件
3. 复用 `e2e-backend.sh` 启动后端
4. 专门的小程序 E2E 配置

## 总结

当前本地联调能力：
- ✅ 后端 API 完全复用
- ✅ API 验证脚本完全适用  
- ✅ 构建链完整可复现
- ⚠️ 小程序 UI 测试需手动（无 Playwright 覆盖）

建议内测前完成：
1. 四条核心链路手动点验
2. API 层自动化验证
3. 构建链完整性验证