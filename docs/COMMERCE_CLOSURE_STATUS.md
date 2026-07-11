# 商业闭环状态 & 支付内测验收对照

> **记录日期：** 2026-07-11  
> **用途：** 上线内测前逐项对照检查；后续迭代更新本文件顶部的记录日期与状态表。

---

## 1. 商业闭环总览

```
┌─────────────────────────────────────────────────────────────────┐
│  tier 门控 + 配额分层        ✅  已落地                          │
│  职位发布 + 销售咨询闭环      ✅  已落地                          │
│  支付骨架 + Stub 封堵         ✅  已落地（架构层漏洞已堵）          │
│  真收款（微信实单）           🟡  骨架就绪，待凭证 + 0.01 元验收    │
│  PlanetX 增长漏斗（C 端）     ❌  待阶段三                        │
│  Pro 分析看板                 ❌  待 P1                           │
│  私有化 Docker 包             ❌  待 P2                           │
└─────────────────────────────────────────────────────────────────┘
```

### 1.1 模块完成度对照表

| 模块 | 状态 | 关键文件 | 验证方式 |
|------|------|----------|----------|
| Tier 硬门控 `@require_tier` | ✅ | `backend/src/api/auth/decorators.py` | `tests/test_tier_gating.py` |
| 候选人池分层 free=0 / sup=20 / pro=200 | ✅ | `backend/src/utils/tier_limits.py` | 用例 `test_supporter_can_access_candidates` |
| 职位发布 CRUD + 匹配 | ✅ | `backend/src/api/routes/job_post_routes.py` | 用例 `test_job_post_limits_by_tier` |
| 企业联系销售 | ✅ | `enterprise_routes.py` → `sales_inquiries` 表 | 用例 `test_contact_sales_creates_inquiry` |
| 前端 Pricing 双模式 | ✅ | `frontend/packages/saas/src/features/pricing/Pricing.tsx` | 目视：stub 直升 / 生产二维码 |
| 订单 + 订阅表 | ✅ | `backend/src/db/manager.py` `orders` / `subscriptions` | `tests/test_payment_guard.py` |
| Stub 升级门控 | ✅ | `backend/src/api/routes/payment_routes.py` | 用例 `test_stub_upgrade_blocked_when_disabled` |
| 微信支付骨架 | ✅ | `backend/src/payment/wechat_pay.py` | 用例 `test_wechat_order_*` |
| 微信实单收款 | 🟡 | 同上 + 商户凭证 | 0.01 元实单 + notify 回调 |
| PlanetX tier 卡片 | ❌ | `frontend/packages/planetx/.../HubScreen.tsx` | — |
| 订阅到期自动降级 cron | ❌ | — | — |

### 1.2 Tier 功能矩阵（代码真源）

| Tier | 职位发布 | 候选人池 | 查看匹配 | 分析看板 |
|------|---------|---------|---------|---------|
| free | 0 | 0（需先建企业） | ❌ | ❌ |
| supporter | 3 | 20 | ✅ | ❌ |
| pro | 20 | 200 | ✅ | ❌（待建） |
| enterprise | 不限 | 不限 | ✅ | ✅（待建） |

真源：`backend/src/utils/tier_limits.py`

### 1.3 定价（CN 区）

| Tier | 月费 | 微信下单金额（分） |
|------|------|-------------------|
| supporter | ¥9.9 | 990 |
| pro | ¥29.9 | 2990 |

真源：`backend/contracts/payment.v1.json` + `payment_routes.py` `TIER_PRICE_FEN`

---

## 2. 环境配置对照

### 2.1 支付模式开关（最关键）

| 变量 | 开发/内测 Stub | 生产/实单验收 | 说明 |
|------|---------------|--------------|------|
| `PAYMENT_STUB_MODE` | `true` | **`false`** | 生产必须为 `false`，否则可免费升 tier |

**行为对照：**

| 端点 | `PAYMENT_STUB_MODE=true` | `PAYMENT_STUB_MODE=false` |
|------|--------------------------|---------------------------|
| `POST /v1/payment/upgrade` | 200 直接升级 + 审计订单 | **402** `payment_required` |
| `POST /v1/payment/wechat/order` | **400** `stub_mode` | 201 返回 QR/JSAPI 参数 |
| `POST /v1/payment/wechat/notify` | 可调用（验签） | 回调验签 → 升级 tier → 写 subscription |
| `GET /v1/payment/plans` | 响应含 `stub_mode: true` | 响应含 `stub_mode: false` |

### 2.2 微信支付凭证（实单验收必填）

| 变量 | 必填 | 示例 / 说明 | 代码引用 |
|------|------|------------|----------|
| `WECHAT_MCHID` | ✅ | 商户号，如 `1234567890` | `config.py` L99 |
| `WECHAT_APPID` | ✅ | 公众号/小程序 AppID（与登录可共用） | `config.py` L33 |
| `WECHAT_API_V3_KEY` | ✅ | API v3 密钥（32 位） | `config.py` L100 |
| `WECHAT_SERIAL_NO` | ✅ | 商户 API 证书序列号 | `config.py` L101 |
| `WECHAT_PRIVATE_KEY_PATH` | ✅ | 商户私钥 PEM 文件绝对路径 | `config.py` L102 |
| `WECHAT_NOTIFY_URL` | ✅ | 公网 HTTPS 回调地址（见 §2.4） | `config.py` L103 |

> **注意：** 旧文档 `TENCENT_CLOUD_COMMERCE.md` 使用 `WECHAT_PAY_*` 前缀；**代码真源为 `WECHAT_*`（无 `PAY` 中缀）**，以本表为准。

### 2.3 微信登录（与支付 AppID 可共用）

| 变量 | 开发 | 生产内测 |
|------|------|---------|
| `WECHAT_APPID` | mock 或真实 | 真实 |
| `WECHAT_APP_SECRET` | mock 或真实 | 真实 |
| `WECHAT_DEV_MODE` | `true`（跳过 code2session） | **`false`** |

### 2.4 回调 URL（备案域名）

**代码注册路径：** `POST /v1/payment/wechat/notify`

```
# 推荐（与 SZBOLENT 切域 checklist 对齐）
WECHAT_NOTIFY_URL=https://api.szbolent.com.cn/v1/payment/wechat/notify
```

> ⚠️ 旧 checklist 写的是 `/v1/payment/notify/wechat`（路径顺序不同），部署时以 **代码真源** `/v1/payment/wechat/notify` 为准，并在微信商户平台配置一致。

### 2.5 企业销售通知（可选）

| 变量 | 必填 | 说明 |
|------|------|------|
| `SALES_WEBHOOK_URL` | 否 | 钉钉/飞书 webhook；未配置时仅写 DB + 日志 |

### 2.6 Python 依赖（实单 RSA 签名）

```bash
pip install cryptography   # wechat_pay.py RSA 签名；未安装时走 skeleton 回退
```

### 2.7 开发环境 `.env` 模板（最小可跑）

```bash
# --- Payment ---
PAYMENT_STUB_MODE=true

# --- WeChat Pay（实单验收时改为 false 并填全）---
# PAYMENT_STUB_MODE=false
# WECHAT_MCHID=
# WECHAT_APPID=
# WECHAT_API_V3_KEY=
# WECHAT_SERIAL_NO=
# WECHAT_PRIVATE_KEY_PATH=/secure/apiclient_key.pem
# WECHAT_NOTIFY_URL=https://api.szbolent.com.cn/v1/payment/wechat/notify

# --- WeChat Login ---
WECHAT_APPID=your-appid
WECHAT_APP_SECRET=your-app-secret
WECHAT_DEV_MODE=true

# --- Enterprise sales（可选）---
# SALES_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
```

---

## 3. 内测前支付验收清单

### Phase A — 本地 / CI（无需商户号）

- [ ] `cd backend && .venv/bin/python -m pytest tests/test_payment_guard.py -v` — 9 passed
- [ ] `cd backend && .venv/bin/python -m pytest tests/test_tier_gating.py -v` — 7 passed
- [ ] `cd backend && .venv/bin/python -m pytest tests/test_payment_plans.py -v` — 5 passed
- [ ] `PAYMENT_STUB_MODE=true` 时 `POST /v1/payment/upgrade` 返回 200
- [ ] `PAYMENT_STUB_MODE=false` 时 `POST /v1/payment/upgrade` 返回 **402**
- [ ] `PAYMENT_STUB_MODE=false` 且无凭证时 `POST /v1/payment/wechat/order` 返回 **503** `payment_not_configured`
- [ ] Pricing 页 `GET /v1/payment/plans` 响应含 `stub_mode` 字段

### Phase B — 预发 / 备案域（需商户号，0.01 元实单）

- [ ] `PAYMENT_STUB_MODE=false` 已写入生产 `.env`
- [ ] §2.2 六项微信凭证全部非空
- [ ] `WECHAT_NOTIFY_URL` 指向备案 API 域且微信商户平台已登记同路径
- [ ] `cryptography` 已安装，日志无 "skeleton fallback" 警告
- [ ] `POST /v1/payment/wechat/order` 返回 `qr_code_url` 或 `jsapi_params`（非 stub）
- [ ] 扫码支付 0.01 元后 `POST /v1/payment/wechat/notify` 收到回调
- [ ] `users.tier` 升级为 `supporter` 或 `pro`
- [ ] `orders.status` 变为 `paid`，`subscriptions.expires_at` 已写入
- [ ] `GET /v1/payment/status` 返回 `expires_at` 非 null
- [ ] 再次 `POST /v1/payment/upgrade` 仍返回 402（不可绕过）

### Phase C — 商业闭环端到端

- [ ] supporter 用户可 `POST /v1/job-posts`（≤3 个）
- [ ] supporter 用户可 `GET /v1/enterprise/candidates`（≤20 人）
- [ ] free 用户访问候选人 API 返回 403
- [ ] Pricing 企业版「联系我们」提交成功写入 `sales_inquiries`

---

## 4. 验收命令速查

```bash
# 健康检查
curl -sf https://api.szbolent.com.cn/health

# 套餐 + stub 模式标志
curl -s "https://api.szbolent.com.cn/v1/payment/plans?region=CN" | jq '{region, stub_mode, plans: [.plans[].tier]}'

# Stub 门控（需 JWT）
TOKEN="<access_token>"
curl -s -X POST "https://api.szbolent.com.cn/v1/payment/upgrade" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier":"supporter"}' | jq '{status: .error // "ok", tier}'

# 微信下单（生产模式）
curl -s -X POST "https://api.szbolent.com.cn/v1/payment/wechat/order" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier":"supporter","trade_type":"NATIVE"}' | jq .

# 订阅状态
curl -s "https://api.szbolent.com.cn/v1/payment/status?region=CN" \
  -H "Authorization: Bearer $TOKEN" | jq '{tier, status, expires_at, stub_mode}'

# 后端测试套件
cd backend && .venv/bin/python -m pytest \
  tests/test_payment_guard.py \
  tests/test_tier_gating.py \
  tests/test_payment_plans.py -v --tb=short
```

---

## 5. 关键 API 索引

| 方法 | 路径 | 鉴权 | 用途 |
|------|------|------|------|
| GET | `/v1/payment/plans` | 无 | 套餐列表 + `stub_mode` |
| GET | `/v1/payment/status` | JWT | 当前 tier + 订阅到期 |
| POST | `/v1/payment/upgrade` | JWT | Stub 直升（生产 402） |
| POST | `/v1/payment/wechat/order` | JWT | 创建微信订单 |
| POST | `/v1/payment/wechat/notify` | 验签 | 微信回调 |
| POST | `/v1/enterprise/contact-sales` | 可选 JWT | 企业版咨询 |
| POST | `/v1/job-posts` | JWT + supporter+ | 发布职位 |

---

## 6. 关联文档

| 文档 | 内容 |
|------|------|
| `docs/TENCENT_CLOUD_COMMERCE.md` | 腾讯云商业化总体规划（部分变量名已过时，见 §2.2） |
| `docs/SZBOLENT_COM_CN_CUTOVER_CHECKLIST.md` | 备案域切域 + Phase 4 支付 |
| `docs/PAYMENT_TIER_CONTRACT.md` | Tier 与配额契约 |
| `backend/contracts/payment.v1.json` | 定价契约真源 |
| `backend/.env.example` | 环境变量模板（含支付段） |

---

## 7. 变更日志

| 日期 | 变更 |
|------|------|
| 2026-07-11 | 初版：记录 tier 差异化 + 微信支付骨架 + Stub 门控状态；整理内测验收配置对照 |
