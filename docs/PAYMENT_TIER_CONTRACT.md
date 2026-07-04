# 支付与 Tier 契约存档（双仓统一执行标准）

> **归档日期：** 2026-07-04  
> **对话结论：** Jason × Cursor 联调会话 · 支付正道 + 区域定价 + tier 拉通  
> **机器可读真源：** `backend/contracts/payment.v1.json`（**仅 looma-zervi 仓维护**）  
> **关联文档：** [TENCENT_CLOUD_COMMERCE.md](./TENCENT_CLOUD_COMMERCE.md) · [DECISION_RESPONSE.md](./DECISION_RESPONSE.md) · [DUAL_REPO_WORK_GUIDE.md](./DUAL_REPO_WORK_GUIDE.md)

---

## 0. 给双仓的 TL;DR

| 项 | 统一标准 |
|----|----------|
| **收银真源** | Looma `/v1/payment/*` + JWT tier |
| **门户 UI** | szbolent-portal / saas Pricing **消费 API**，不硬编码价格 |
| **tier 枚举** | `free` · `supporter` · `pro` · `enterprise` |
| **supporter 定价** | 国内 **¥9.9/月** · 境外 **$1.99/月**（同 tier，不同 region） |
| **废弃** | `basic` → 映射 `supporter`；**不复活** `tatha-frontend` 收银 |
| **WP ErphpDown** | 仅博客/modown 站内 VIP，**不是**主产品收银台 |

---

## 1. 架构决策（已拍板，勿走临时替代）

### 1.1 正道

```text
用户 → portal / saas Pricing（唯一定价 UI）
         ↓
      Looma GET /v1/payment/plans?region=CN|US
         ↓
      下单 / Stub upgrade → tier 写入 DB → JWT 刷新
         ↓
      配额 / RAG / 诗词等按 tier 生效
```

### 1.2 明确不做

| 方案 | 结论 | 原因 |
|------|------|------|
| `tatha-frontend` 直接跳转支付 | ❌ | 无真实支付链；API/token 与 Looma 脱节；RAG 已并入 looma |
| 跳 WordPress ErphpDown 作为主收银 | ❌ | 第二套会员体系，与 JWT tier 真源冲突 |
| portal 硬编码 tier 名/价格 | ❌ | 已与 backend 不一致，维护分叉 |
| 临时改 tatha 链接凑合演示 | ❌ | 制造第五套命名，与 S0 契约方向相反 |

### 1.3 内测 Stub 是正道上的台阶

当前 `POST /v1/payment/upgrade` 为 **Stub**（无真实收款），但路径正确。P1 微信支付 / P2 Stripe 在 **同一条 API 链** 上替换实现，不另起架构。

---

## 2. Tier 与命名（全局统一）

### 2.1 合法 tier（JWT / DB / API 唯一枚举）

```text
free → supporter → pro → enterprise
```

| tier | 自助购买 | 说明 |
|------|----------|------|
| `free` | — | 注册默认 |
| `supporter` | ✅ | 低档赞助 / 去主要配额限制 |
| `pro` | ✅ | 全功能订阅 |
| `enterprise` | ❌ | 联系销售，人工开通 |

### 2.2 废弃别名

| 旧名 | 新名 | 来源 |
|------|------|------|
| `basic` | `supporter` | 旧 Tatha 静态页 URL 参数 |

**API 不接受 `basic`**。前端若见历史链接 `?tier=basic`，应转换为 `supporter` 再调 Looma。

### 2.3 历史命名对照（勿再使用）

| 来源 | 曾用命名 | 现标准 |
|------|----------|--------|
| tatha-frontend | `basic` / `pro`，¥99 / ¥299 | **不参与** Szbolent 契约 |
| saas Pricing（改前） | 缺 `supporter`，仅 free/pro/enterprise | 已改为拉 API |
| Looma backend | `supporter` / `pro` | ✅ 真源 |

---

## 3. 区域定价（购买力分区，非机械汇率）

**原则：** tier 身份全球一致；**价格按 region 分叉**；数字体现各市场可接受价，不是当日汇率 1:1 换算。

### 3.1 已锁定价格（v1.0.0）

| tier | region=CN | region=US | plan_id 示例 |
|------|-----------|-----------|--------------|
| free | ¥0 | $0 | `free_monthly_cn` / `_us` |
| **supporter** | **¥9.9/月** | **$1.99/月** | `supporter_monthly_cn` / `_us` |
| pro | ¥29.9/月 | $5.99/月 | `pro_monthly_cn` / `_us` |
| enterprise | 联系销售 | Contact sales | 无自助 plan_id |

**说明：**

- **supporter ¥9.9 ↔ $1.99**：Jason 2026-07-04 拍板；$1.99 为常见冲动消费档，¥9.9 为国内赞助档。
- **pro $5.99**：按 CNY 档位比例（29.9÷9.9≈3）推导；若需调整为 $4.99 / $9.99，**只改** `payment.v1.json` 并双审，UI 自动跟随 API。

### 3.2 支付通道（按 region）

| region | currency | provider | 阶段 |
|--------|----------|----------|------|
| `CN`（默认） | CNY | `wechat` | P0 Stub · P1 微信实付 |
| `US` | USD | `stripe` | P2 跨境 |

---

## 4. API 契约（执行标准）

### 4.1 机器可读真源

```text
looma-zervi/backend/contracts/payment.v1.json
```

- **变更流程：** 改 JSON → looma PR → 通知 portal → portal 仅消费 API（可对照 JSON 做类型，**不在 portal 复制第二份 JSON 真源**）
- **TypeScript 镜像：** `frontend/packages/shared-core/src/types/payment.ts`（须与 JSON 双审同步）

### 4.2 已实现端点（looma main 工作区）

| 方法 | 路径 | 行为 |
|------|------|------|
| GET | `/v1/payment/plans?region=CN\|US` | 返回 `region`、`currency`、`payment_provider`、`plans[]` |
| GET | `/v1/payment/status` | 当前用户 tier + 对应 region 的 plan |
| POST | `/v1/payment/upgrade` | Stub：`{ "tier": "supporter" \| "pro" }`，返回新 JWT |

**plans 单条字段：** `tier`, `name`, `price_monthly`, `currency`, `region`, `plan_id`, `features`, `upgradable`

**region 解析顺序：** 查询参数 `region` → `Accept-Language`  hint → 默认 `CN`

### 4.3 验证命令

```bash
# 国内 supporter 应为 9.9 CNY
curl -s 'http://localhost:5200/v1/payment/plans?region=CN' | jq '.plans[] | select(.tier=="supporter")'

# 境外 supporter 应为 1.99 USD
curl -s 'http://localhost:5200/v1/payment/plans?region=US' | jq '.plans[] | select(.tier=="supporter")'
```

### 4.4 P1 目标端点（见 TENCENT_CLOUD_COMMERCE §4.2）

- `POST /v1/payment/orders` — 统一下单
- `POST /v1/payment/notify/wechat` — 微信回调
- 生产环境：`POST /v1/payment/upgrade` → **410**（仅内测 Stub）

---

## 5. 代码落点（2026-07-04 已改）

| 仓 | 路径 | 状态 |
|----|------|------|
| looma | `backend/contracts/payment.v1.json` | ✅ 新建 v1.0.0 |
| looma | `backend/src/payment/plans.py` | ✅ 契约加载器 |
| looma | `backend/src/api/routes/payment_routes.py` | ✅ region-aware |
| looma | `backend/tests/test_payment_plans.py` | ✅ CN/US 价格断言 |
| looma | `frontend/packages/shared-core/src/types/payment.ts` | ✅ 类型 + 常量 |
| looma | `frontend/packages/saas/.../Pricing.tsx` | ✅ 拉 API，含 supporter 档 |
| portal | `src/api/looma.ts` | ⬜ szbenyx P0-P2 |
| portal | `src/views/Pricing.vue`（或 Services） | ⬜ szbenyx P0-P3 |

---

## 6. 双仓分工与待办

### 6.1 looma-zervi（Surface / Jason）

- [x] **PAY-C1** `payment.v1.json` v1.0.0 + backend 加载
- [x] **PAY-C2** saas Pricing 消费 `/v1/payment/plans?region=CN`
- [ ] **PAY-L1** P1 微信支付替换 Stub（`TENCENT_CLOUD_COMMERCE` P1）
- [ ] **PAY-L2** 合并含 PAY-C1/C2 的 PR 至 `main` 并 push GitHub
- [ ] **PAY-L3** `verify-closed-loop.sh` 可选增加 plans 价格断言

### 6.2 szbolent-portal（szbenyx）

- [ ] **PAY-P1** 阅读本文 + `payment.v1.json`（looma 仓）
- [ ] **PAY-P2** 新建 `src/api/looma.ts`：`getPlans(region)` / `upgrade` / auth
- [ ] **PAY-P3** Pricing 页 **只渲染 API 返回**，默认 `region=CN`
- [ ] **PAY-P4** 禁止 portal 使用 `basic`、禁止硬编码 ¥99/¥299（Tatha 旧价）
- [ ] **PAY-P5** P1 与 looma 微信回调 URL 对齐后再接实付

### 6.3 共用规则

1. **tier 变更只来自 Looma**（Stub 或已支付订单），portal 不写 tier。  
2. **契约变更**须两仓 PR 描述互链，并 bump `payment.v1.json` 的 `version`。  
3. **诗词契约**走 `poetry.v1.json`；**支付契约**走 `payment.v1.json` — 互不混用字段。

---

## 7. 与周边系统边界

| 系统 | 角色 |
|------|------|
| **Looma** | tier / JWT / 支付 API 真源 |
| **szbolent-portal / saas** | Pricing UI + 登录态 + 调起支付 |
| **WordPress + ErphpDown** | 博客、modown 主题内购；与 Looma tier **未定义同步** |
| **tatha-frontend** | 历史静态预览；**归档参考 UI 即可**，不接入 Szbolent 生产 |
| **小程序** | 同 JWT tier；支付 P1 后走 `/v1/payment/orders` |

---

## 8. 修订记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-07-04 | 1.0.0 | 首版：正道架构、tier 枚举、CN ¥9.9 / US $1.99 supporter、契约 JSON + API + saas 对齐 |

---

## 9. szbenyx 签收

- [ ] 已 pull looma 含 `payment.v1.json` 的分支  
- [ ] 已读 §0–§4，Pricing 实现按 §6.2 执行  
- [ ] 已在 PR 或 issue 回复 tier/区域价无异议（或列出修改意见）
