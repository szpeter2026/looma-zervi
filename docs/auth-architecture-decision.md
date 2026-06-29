# 认证架构修订研讨记录：Supabase 砍掉，looma JWT 自签发

> **日期**: 2026-06-29  
> **研讨人**: Peter（szbenyx） + 嘟嘟（AI 助手）  
> **文档性质**: 决策研讨过程记录，供团队对齐  
> **修订结论**: 小程序走 CloudBase openid → looma JWT，Web 走 email/password → looma JWT，认证统一收敛到 looma 自签 JWT。`/v1/auth/bridge` 留着接口但 MVP 不实现，等需要 Web 社交登录时再接 Supabase。

---

## 一、原方案回顾（5份重构文档的设计）

### 1.1 原始认证架构

5份重构文档（分工方案、事实论证、修正分工、开发框架、规划落地）统一设计的认证架构是：

```
用户注册/登录 → Supabase Auth（签发 JWT）
    → 前端拿到 Supabase JWT
    → 调 looma /v1/auth/bridge（或 /v1/auth/sync）
    → looma 后端验证 Supabase JWT 签名 + 查/建用户
    → looma 签发 looma token
    → 后续所有请求用 looma token
```

核心设计意图：**Supabase 负责注册/登录/邮箱验证等成熟功能，looma 只做桥接和签发自己的 token**。这样两端的用户身份统一到 looma 体系下。

### 1.2 原方案的 P0 任务

| P0 项 | 内容 | 依赖 |
|--------|------|------|
| AUTH_STUB 安全修复 | 把 `TATHA_AUTH_STUB` 环境变量控制的桩认证换成真实 JWT 验证 | 需实现 `_verify_supabase_jwt` |
| supabase_uid 映射字段 | user 表加 `supabase_uid`，桥接时写入 | 需 Supabase JWT 解码 |
| DNSPod 排查 | 修复 GET+Bearer 请求被 302 重定向的问题 | 无外部依赖 |

### 1.3 原方案的设计依据（来自"事实依据论证"文档）

- **行业类比**: Supabase 自己在 YC 期间花 3 个月升级 Auth（从早期版 → GoTrue），论证"认证统一是 MVP 到规模化之间最关键的一步"
- **代码实锤**: PlanetX 用 Supabase 直连认证，T空间用 looma API 认证，两套体系让转化链路从根上断了
- **论证逻辑**: 不删除 Supabase，让 Supabase 降级为 JWT 签发器，数据同步到 looma 后不再直连存储

---

## 二、变更触发点：CloudBase 入局

### 2.1 问题起点

Peter 提出："腾讯云开发（CloudBase）里面新建集成，对个人开发者来说性价比如何？"

这个问题的本质是：**要不要把核心后端也迁到 CloudBase？**

### 2.2 第一轮研讨结论：CloudBase 不做核心后端

经过对 CloudBase 定价文档和 GenzLTD 重构文档的交叉分析，得出 **3 个致命硬伤**：

| 硬伤 | 具体表现 | 对重构的影响 |
|------|---------|-------------|
| **无向量数据库** | CloudBase 只有文档型数据库（key-value），不支持向量相似度搜索 | ChromaDB/RAG 核心链路断了——`/v1/ask`、简历匹配、人格分析全部废掉 |
| **无微信支付连接器** | 个人版（19.9元/月）不支持微信支付，标准版（199元/月）才有 | Pro/supporter 付费闭环跑不通——定价模型文档设计的 4档中 supporter ¥9.9/月 和 pro ¥199/月 无法收款 |
| **无 VPC/固定出口IP** | 个人版云函数只能通过公网 HTTP 调外部服务 | 无法从 CloudBase 安全连接阿里云上的 ChromaDB——等于把向量数据库暴露在公网 |

额外硬伤：**认证体系不兼容**——CloudBase 的 openid 登录和 Supabase → looma bridge 完全不兼容。

### 2.3 CloudBase 定位确认

Peter 确认了混合架构方案：

> "国内用户走 CloudBase，只做小程序壳的微信生态入口，其他都按照核心后端自建的方式部署。"

CloudBase 的角色从"可能的核心后端"收窄为 **"小程序端轻量接入层"**：
- 小程序 openid 登录 + 客服验证（免费体验版，0 成本）
- Pro 付费上线时升级标准版（199元/月）拿微信支付连接器
- 核心后端继续跑阿里云（Flask + ChromaDB + SQLite + DeepSeek API）

---

## 三、关键推理：Supabase 为什么可以砍掉

### 3.1 CloudBase 入局后的认证路径变化

原来的认证只有一条路（Web 端）：

```
Web 用户 → Supabase Auth → Supabase JWT → /v1/auth/bridge → looma JWT
```

现在有两条路：

| 用户入口 | 认证方式 | 是否需要 Supabase |
|----------|---------|-----------------|
| 微信小程序 | `wx.login` → CloudBase 拿 openid → looma 验证 | ❌ 不需要 |
| Web 浏览器 | email/password → looma 自验证 | ❌ 不需要 |

**推理链**：

1. 小程序端用 CloudBase openid 认证 → 这条路天然不需要 Supabase
2. Web 端如果 looma 自建 email/password 注册登录 → 这条路也不需要 Supabase
3. 两条路都拿到 looma JWT → 认证统一收敛到 looma 自签发
4. Supabase 在这个架构里变成了**多余的中间层**

### 3.2 逐项论证

#### 论证 1：小程序端不需要 Supabase

```
小程序 wx.login() → 拿到 code
  → 发给 looma /v1/auth/wechat
  → looma 后端调微信 API 用 code 换 openid + session_key
  → looma 查 user 表（by wechat_openid），没有就建新用户
  → looma 签发 JWT 返回
```

CloudBase 的 openid 是微信体系原生身份标识，小程序端直接用 openid → looma JWT 即可。**Supabase 在这条链路里完全没有角色。**

#### 论证 2：Web 端不需要 Supabase

原方案选择 Supabase Auth 的理由是"邮箱验证成熟可靠"。但 MVP 阶段的分析：

| 能力 | Supabase Auth 提供 | looma 自建（bcrypt + PyJWT） | MVP 是否需要 |
|------|-------------------|---------------------------|------------|
| email+password 注册/登录 | ✅ | ✅（100 行代码） | ✅ 需要 |
| 邮箱验证 | ✅ 自动发邮件 | ⚠️ 需自建邮件服务 | ❌ MVP 可跳过 |
| 密码重置 | ✅ 自动流程 | ⚠️ 需自建 | ❌ MVP 可跳过 |
| 社交登录（Google/GitHub） | ✅ | ❌ 不自建 | ❌ MVP 不需要 |
| JWT 签发 | ✅ | ✅（PyJWT） | ✅ 需要 |
| RLS + anon key | ✅ 但是安全风险 | ❌ 不需要 | — 反而更好 |

**结论**: MVP 阶段只需要 email+password 注册登录 + JWT 签发，这 3 件事 looma 用 bcrypt + PyJWT 就能搞定（约 100 行代码）。邮箱验证和密码重置可以后续迭代——国内用户更习惯手机号/微信登录，邮箱验证优先级本来就低。

#### 论证 3：Supabase 作为中间层的代价

| 代价项 | 具体影响 |
|--------|---------|
| **额外依赖** | 前端需要 `@supabase/supabase-js`，后端需要 `_verify_supabase_jwt`，环境变量需要 `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `SUPABASE_JWT_SECRET` |
| **安全风险** | anon key 硬编码在前端（原代码实锤：`planetxStore.ts` 第 19-20 行），RLS 是唯一防线 |
| **调试复杂度** | 认证错误需要同时排查 Supabase 侧和 looma 侧，两个 JWT 体系叠加 |
| **数据库耦合** | Supabase 的用户数据在 Supabase PostgreSQL 里，looma 的在 SQLite 里，跨库同步是额外工作 |
| **付费限制** | Genzers FREE 计划有限制（50K MAU），用户增长到一定量级需要付费升级 |

#### 论证 4：砍掉 Supabase 后 P0 反而更简单

| 原P0 | 新P0 | 变化 |
|------|------|------|
| AUTH_STUB 安全修复（需对接 Supabase JWT 验证） | looma JWT 自签发实现（PyJWT + bcrypt） | **简化** — 不需要验证外部 JWT |
| supabase_uid 映射字段 | wechat_openid 映射字段 | **简化** — 从"映射外部 ID"变为"存储原生 ID" |
| DNSPod 排查 | DNSPod 排查 | **不变** |

原 P0 需要实现 `_verify_supabase_jwt`（验证 Supabase 签名、解码 JWT、提取 uid），新 P0 只需要实现 `create_token()` 和 `verify_token()`（looma 自己签发、自己验证）。**少了整个外部 JWT 解析链路。**

---

## 四、修订后的认证架构

### 4.1 三条认证路径

```
路径 A（小程序端）:
  wx.login() → code → /v1/auth/wechat → openid换token → looma JWT

路径 B（Web端）:
  email+password → /v1/auth/register 或 /v1/auth/login → bcrypt验证 → looma JWT

路径 C（未来可选）:
  Google/GitHub 社交登录 → Supabase Auth → /v1/auth/bridge → Supabase JWT换looma JWT
  ⚠️ MVP 不实现，等需要 Web 社交登录时才接入
```

### 4.2 统一收敛点：looma JWT

无论哪条路径，最终用户手里拿到的都是 **looma 自签 JWT**：

```python
# jwt_handler.py 签发逻辑（已实现）
payload = {
    "user_id": user_id,
    "email": email,           # Web 用户有，小程序用户可能为空
    "wechat_openid": openid,  # 小程序用户有，Web 用户为空
    "tier": tier,             # guest / free / supporter / pro
    "role": role,             # user / admin / enterprise
    "exp": datetime.utcnow() + timedelta(hours=24),
}
token = jwt.encode(payload, LOOMA_JWT_SECRET, algorithm="HS256")
```

### 4.3 User 表设计变更

**原设计**（Supabase 为核心）:

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    supabase_uid TEXT UNIQUE,  -- Supabase 的 UUID
    ...
);
```

**新设计**（looma 为核心，支持多入口）:

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,           -- looma user_id（自生成 UUID）
    email TEXT UNIQUE,             -- Web 注册（可空）
    password_hash TEXT,            -- Web 注册（可空）
    wechat_openid TEXT UNIQUE,     -- 小程序登录（可空）
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

设计要点：
- `email` 和 `wechat_openid` 都**可空**——Web 用户没 openid，小程序用户没 email
- 绑定后两个都有——跨端账号统一
- **不需要 `supabase_uid` 字段**——Supabase MVP 不接入

### 4.4 跨端账号绑定

用户可能先在 Web 注册（email），后来又用小程序（openid）。绑定流程：

```
小程序用户（已有 openid → looma JWT）
  → 小程序里点"绑定邮箱"
  → 输入 email + password
  → /v1/auth/bind（需要 JWT）
  → looma 把 wechat_openid 关联到已有 user_id
  → 两端身份统一
```

这是国内 App 的标准模式（绑定微信/绑定手机号），用户习惯没问题。

---

## 五、`/v1/auth/bridge` 的定位变化

### 5.1 原定位（核心入口）

```
Supabase JWT → /v1/auth/bridge → looma token
↑ 这是整个认证统一的核心路径
```

### 5.2 新定位（可选接口）

| 阶段 | bridge 状态 | 理由 |
|------|------------|------|
| **MVP** | 不实现（返回 501 Not Implemented） | 小程序用 wechat 路径，Web 用 login 路径，bridge 没有使用场景 |
| **需要 Web 社交登录时** | 恢复实现 | 接入 Supabase Auth 做 Google/GitHub 登录，bridge 把 Supabase JWT 换成 looma JWT |

### 5.3 为什么留着接口不删

1. **向后兼容预留**——如果未来确实需要 Web 端社交登录，bridge 是最自然的接入方式
2. **团队共识缓冲**——原5份文档都以 bridge 为核心设计，突然删除可能引起团队困惑；返回 501 比删除更温和
3. **代码骨架已搭**——框架里的 `auth_routes.py` 已有 bridge 端点（返回 501），不需要额外工作

---

## 六、修订对重构文档的影响

### 6.1 受影响的部分

| 原文档 | 原设计 | 修订后 | 变化程度 |
|--------|--------|--------|---------|
| **事实依据论证** | "Supabase 降级为 JWT 签发器" | "Supabase MVP 不接入" | **中等** — 论证方向从"降级"变为"移除"，但核心论点（认证必须统一）不变 |
| **分工方案** | Phase 2 Jason 做 Supabase → looma 桥接 | Phase 2 Jason 做 planetxStore → looma API 改造 + `/v1/game/*` 路由 | **小** — Jason 的后端工作从 auth 桥接改为 game 路由，工作量不变 |
| **分工方案** | `/v1/auth/*` 联合 ownership | `/v1/auth/*` 仍联合 ownership | **不变** — wechat 路径 + login 路径 + bridge(501) 仍需要双方对齐 |
| **开发框架** | `supabase_uid` 字段 | `wechat_openid` 字段 | **小** — 字段名变了，本质是"存储外部身份标识" |
| **规划落地** | P0: AUTH_STUB + supabase_uid | P0: looma JWT 实现 + wechat_openid + DNSPod | **简化** — P0 工作量减少 |

### 6.2 不受影响的部分

| 部分 | 原设计 | 修订后 | 理由 |
|------|--------|--------|------|
| 双品牌架构 | PlanetX + T空间 | 不变 | 认证路径不影响品牌划分 |
| 包隔离规则 | planetx/saas/shared/miniprogram | 不变 | 包结构跟认证方式无关 |
| 后端路由 ownership | game=Jason, enterprise=szbenyx | 不变 | 只是 auth 路径变了 |
| DB schema（非 users 表） | game_profiles/fleets/enterprises/... | 不变 | 只有 users 表变了 |
| Docker 部署方案 | Flask+ChromaDB+nginx | 不变 | 后端部署架构不变 |
| CloudBase 定位 | 小程序壳 | 不变 | 这是触发修订的原因，本身不变 |

---

## 七、修订结论（一句话）

> **架构可行，Supabase 砍掉。小程序走 CloudBase openid → looma JWT，Web 走 email/password → looma JWT，认证统一收敛到 looma 自签 JWT。`/v1/auth/bridge` 留着接口但 MVP 不实现，等需要 Web 社交登录时再接 Supabase。P0 反而更简单了。**

---

## 八、何时把 Supabase 加回来

只有一种情况：**需要 Web 端社交登录**（Google/GitHub/微信扫码登录 Web 端）。

届时恢复路径：
1. Web 端接入 Supabase Auth（社交登录提供商）
2. `/v1/auth/bridge` 恢复——Supabase JWT → looma JWT
3. users 表加 `supabase_uid` 字段
4. 社交登录用户通过 bridge 拿到 looma JWT，与已有用户可绑定

**这不是 MVP 的事**。MVP 阶段 Web 用 email/password 足够验证产品。

---

## 九、团队对齐要点

### 需要团队确认的 3 个决策

| # | 决策项 | 选项 | 建议选择 |
|---|--------|------|---------|
| 1 | Supabase MVP 是否接入 | A: 接入（原方案）/ B: 不接入（修订方案） | **B** |
| 2 | `/v1/auth/bridge` MVP 状态 | A: 完整实现 / B: 返回 501 / C: 删除端点 | **B** |
| 3 | users 表身份字段 | A: `supabase_uid` / B: `wechat_openid` / C: 通用 `external_id + external_provider` | **B**（MVP 只微信+邮箱，没必要过度设计） |

### Jason 需要知道的变化

| 原任务 | 新任务 | 影响 |
|--------|--------|------|
| planetxStore 登录流程: Supabase JWT → /v1/auth/sync → looma token | planetxStore 登录流程: email/password → /v1/auth/login → looma JWT（Web端） | **简化** — 不需要 Supabase 客户端 |
| 小程序登录: 需对接 Supabase | 小程序登录: `wx.login` → `/v1/auth/wechat` → looma JWT | **简化** — 直接用 openid |
| Phase 2 后端: auth 桥接 | Phase 2 后端: `/v1/game/*` 路由 | **转移** — auth 部分由 szbenyx 完成 |

### szbenyx 需要追加的任务

| 新任务 | 说明 | 代码量估算 |
|--------|------|-----------|
| `/v1/auth/register` | email + password + bcrypt 哈希 → looma JWT | ~30 行 |
| `/v1/auth/login` | email + password 验证 → looma JWT | ~20 行 |
| `/v1/auth/wechat` | code → openid → 查/建用户 → looma JWT | ~40 行 |
| `/v1/auth/bind` | 绑定 email 到已有 openid 用户 | ~20 行 |
| jwt_handler.py | `create_token()` + `verify_token()` + `@jwt_required` | ~50 行 |
| users 表 schema | 加 `wechat_openid` + `password_hash`，去掉 `supabase_uid` | schema 变更 |

**总计**: 约 160 行新增代码，比原方案的 Supabase JWT 验证 + 桥接逻辑（~200 行）还少。

---

## 附录：研讨过程时间线

| 时间 | 事件 |
|------|------|
| 上午 | Peter 提问："腾讯云开发 CloudBase 新建集成，对个人开发者性价比如何？" |
| 上午 | 分析 CloudBase 4档套餐 + GenzLTD 5份重构文档交叉对比，得出3个致命硬伤 |
| 上午 | Peter 确认混合架构方案："国内用户走 CloudBase，只做小程序壳" |
| 下午 | 深入研讨 CloudBase openid + looma 自建认证 vs Supabase → looma bridge，得出"Supabase MVP 可移除"结论 |
| 下午 | Peter 确认："开始搭建框架结构，然后逐一迁移源码验证" |
| 下午 | 完成 looma-zervi 96文件框架骨架搭建（含修订后的认证架构） |

---

> **文档维护**: 此记录反映 2026-06-29 的研讨结论。如后续有新决策（如恢复 Supabase 接入），请在此文档追加修订记录。
