# Looma 统一底座 · 双品牌开发规划

> **版本**: v1.0  
> **日期**: 2026-06-29  
> **定位**: PlanetX (C端 AI 求职陪伴) + T空间 (B端 SaaS) → 共有后端 looma  
> **核心原则**: looma 是唯一数据后端，Supabase 降级为纯 JWT 签发；所有业务数据走 looma，打通 C→B 转化链路

---

## 一、现状诊断

### 1.1 架构混乱点

| 问题 | 表现 | 影响 |
|------|------|------|
| **双认证体系** | PlanetX 用 Supabase JWT；T空间/Panel 用 looma token | 同一用户两套账号，身份断裂，转化链路不通 |
| **数据孤岛** | PlanetX 游戏数据（人格测试、舰队、XP）存在 Supabase profiles 表；looma 完全不知道 | looma 无法做用户画像、精准推荐、转化分析 |
| **包结构混合** | `/planetx` 和 `/panel/*` 塞在同一个 `@looma/web` 里 | 全局 CSS 冲突、构建体积膨胀、路由守卫逻辑混乱 |
| **API 契约不匹配** | 后端 login 返回 `{user_id, tier}`；前端期望 `{user, UserProfile}` | 登录后必须调 `/v1/auth/profile`（后端未实现）才能拿到用户信息 |
| **GET+Bearer 被拦截** | `api.genz.ltd` 的 GET 请求带 Authorization 被 DNSPod 302 | 国内用户无法通过 profile/quota 验证 |

### 1.2 代码归属速查

```
PlanetX (C端)                     T空间/SaaS (B端)                共享
──────────────────               ──────────────────              ──────────────
pages/planetx/ (7 files)         pages/panel/ (10 files)         pages/auth/ (2)
components/planetx/ (6)          components/layout/ (2)          components/common/ (3)
stores/planetxStore.ts           stores/authStore.ts             @looma/shared (全包)
types/planetx/                   AuthGuard.tsx                   api/client.ts
暗色主题 #080810                  侧边栏仪表盘                    环境变量 .env
Supabase 直连                    looma JWT                      常量 constants/
移动端优先 max-w-[420px]         Web 桌面端优先
```

---

## 二、目标架构

### 2.1 三品牌定位

| 品牌 | 角色 | 用户 | 核心价值 | 入口 |
|------|------|------|----------|------|
| **PlanetX** | C端引流与体验 | 求职者（大学生/职场新人） | 乐趣 → 人格洞察 → 职业方向 | `planetx.genz.ltd` 或主站 `/planetx` |
| **T空间** | B端 SaaS 工具 | HR/猎头/企业管理员 | 效率 → 精准匹配 → 团队管理 | `app.genz.ltd` 或 `/app` |
| **looma** | 共有后端底座 | 两个前端 + Zervi 终端 | AI 推理 → 配额 → 多租户 → 转化数据 | `api.genz.ltd` |

### 2.2 转化链路

```
PlanetX 引流（免费好玩） → 留存（人格报告+舰队社交） → 付费（pro解锁深度报告）
                                                    ↓
                                      企业看到求职者数据 → T空间付费使用
                                                    ↓
                                      企业邀请求职者加入 tenant → 双向锁定
```

### 2.3 前端包结构（目标）

```
frontend/packages/
  ├── shared/          ← 类型 + API factory + 常量（现有，升级）
  │     ├── createPlanetXApi()   ← /v1/game/* + /v1/ask + /v1/referral
  │     ├── createSaasApi()      ← /v1/enterprise/* + /v1/auth/* + /v1/rag/*
  │     ├── createSharedApi()    ← /v1/auth/login/register/profile（共用）
  │     └── shared types + utils + constants
  │
  ├── planetx/         ← C端独立包（从 web 拆出）
  │     ├── vite.config.ts（独立）
  │     ├── .env（VITE_API_BASE + VITE_SUPABASE_URL）
  │     ├── 游戏化 UI 组件（星空暗色主题）
  │     ├── planetxStore → looma API（不再直连 Supabase 数据）
  │     └── 入口：planetx.genz.ltd
  │
  ├── saas/            ← B端独立包（取代原 web）
  │     ├── vite.config.ts（独立）
  │     ├── .env（VITE_API_BASE）
  │     ├── 仪表盘 UI + authStore
  │     └── 入口：app.genz.ltd
  │
  └── miniprogram/     ← 小程序（不变）
```

---

## 三、分阶段开发规划

### Phase 0：产品边界确认（1 天）

**目标**：团队对"哪些功能属于 PlanetX、哪些属于 T空间"达成共识，防止后续开发越界

| 产出 | 内容 | 交付 |
|------|------|------|
| **PlanetX 功能清单** | 人格测试、舰队组队、XP 系统、星际匹配（初版 job match）、分享裂变、深度报告（Pro） | 产品 + 前端 |
| **T空间 功能清单** | 仪表盘、智能问答(RAG)、文档管理、简历解析、职位匹配(精版)、报告生成、企业管理面板、使用统计 | 产品 + 前端 |
| **共享功能清单** | 注册/登录、配额、定价/支付、用户 Profile | 前端 + 后端 |
| **功能归属矩阵** | 每个功能标注 C端/B端/共享 + 优先级 | 全团队签字 |

**关键决策**：

| 决策 | 建议方案 | 理由 |
|------|----------|------|
| Supabase 定位 | **降级为纯 JWT 签发** | 数据统一才能打通转化链路 |
| T空间入口 | **独立域名 `app.genz.ltd`** | 不从 PlanetX OnboardingScreen 进入 |
| PlanetX 游戏数据 | **迁移到 looma `/v1/game/*`** | looma 需要知道用户的人格结果才能做推荐和转化 |
| 小程序归属 | **归 PlanetX** | 求职者手机端是 C端延伸 |

---

### Phase 1：前端拆包分离（3-5 天）

**目标**：`packages/planetx` 和 `packages/saas` 从 `packages/web` 拆出，各自独立 build + dev

#### 1.1 创建 planetx 包

| 步骤 | 操作 | 文件变更 |
|------|------|----------|
| 1 | 创建 `packages/planetx/` 目录结构 | `package.json`, `vite.config.ts`, `tsconfig.json`, `.env` |
| 2 | 迁移 PlanetX 页面 | `pages/planetx/*` → `planetx/src/pages/*` |
| 3 | 迁移 PlanetX 组件 | `components/planetx/*` → `planetx/src/components/*` |
| 4 | 迁移 PlanetX store | `planetxStore.ts` → `planetx/src/stores/planetxStore.ts` |
| 5 | 迁移 PlanetX 类型 | `types/planetx/*` → `planetx/src/types/*` |
| 6 | 创建独立入口 | `planetx/src/main.tsx`, `planetx/src/App.tsx`（只含 `/planetx` 路由） |
| 7 | 配置 Vite | 暗色主题 CSS、独立 proxy 配置、`@looma/shared` alias |

#### 1.2 创建 saas 包

| 步骤 | 操作 | 文件变更 |
|------|------|----------|
| 1 | 将 `packages/web` 重命名/重构为 `packages/saas` | `package.json` name 改为 `@looma/saas` |
| 2 | 删除所有 PlanetX 相关代码 | 移除 `pages/planetx/`, `components/planetx/`, `planetxStore.ts`, `types/planetx/` |
| 3 | 删除 `/planetx`、`/demo`、`/narrative` 路由 | `App.tsx` 只保留 `/login`, `/register`, `/*`（Panel 路由） |
| 4 | 配置独立 Vite | `.env` VITE_API_BASE, proxy → localhost:8000 |
| 5 | authStore 独立化 | 移除 planetx 相关依赖 |

#### 1.3 升级 @looma/shared

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 新增 `createPlanetXApi()` | 封装 `/v1/game/*`, `/v1/referral/*`, `/v1/ask` |
| 2 | 新增 `createSaasApi()` | 封装 `/v1/enterprise/*`, `/v1/auth/profile`, `/v1/quota` |
| 3 | 保留 `createAuthApi()` | 共用 login/register，两端共享 |
| 4 | 常量拆分 | `BRAND_PLANETX`, `BRAND_SAAS` 替代单一 `BRAND` |
| 5 | 类型拆分 | `PlanetXUser` vs `SaasUser` vs 共用 `UserProfile` |

#### 1.4 更新 pnpm-workspace.yaml

```yaml
packages:
  - "packages/*"    # shared, planetx, saas, miniprogram
allowBuilds:
  '@swc/core': true
  '@tarojs/cli': true
  esbuild: true
  swiper: true
verifyDepsBeforeRun: false
```

#### 验收标准

| 标准 | 验证命令 |
|------|----------|
| planetx 独立 build | `cd frontend && pnpm --filter @looma/planetx build` → `dist/` 产物生成 |
| saas 独立 build | `cd frontend && pnpm --filter @looma/saas build` → `dist/` 产物生成 |
| planetx 独立 dev | `pnpm --filter @looma/planetx dev` → localhost:5173 显示 PlanetX 页面 |
| saas 独立 dev | `pnpm --filter @looma/saas dev` → localhost:5174 显示登录页 |
| 无交叉依赖 | planetx 的 bundle 不包含 Sidebar/AppLayout；saas 不包含 StarBackground/XPBar |

---

### Phase 2：统一认证 + 游戏数据回归 looma（5-7 天）

**目标**：PlanetX 不再直连 Supabase 存数据，所有游戏状态通过 looma API 同步

#### 2.1 认证统一方案

```
用户注册/登录 → Supabase JWT 签发 → 前端拿到 JWT
                                    ↓
                        前端拿 JWT 调 looma /v1/auth/sync
                                    ↓
                        looma 验证 JWT → 自动创建 looma 用户 → 返回 looma token
                                    ↓
                        后续所有请求用 looma token（不再用 Supabase JWT）
```

**关键**：注册仍然走 Supabase（它的邮箱验证、密码管理成熟可靠），但数据同步到 looma 后，Supabase JWT 仅用于首次身份验证，之后全部用 looma token。

#### 2.2 planetxStore 改造

| 改造点 | 现在 | 目标 |
|--------|------|------|
| 认证 | `getSupabase()` → `supabase.auth.signUp/signInWithPassword` | Supabase 签发 JWT → 调 looma `/v1/auth/sync` 换 looma token |
| 人格结果 | 写入 Supabase `profiles` 表 | 调 looma `/v1/game/personality_result` |
| 舰队数据 | 读/写 Supabase `fleets` + `fleet_members` | 调 looma `/v1/game/fleet/*` |
| XP/等级 | Supabase `profiles.xp/level` | 调 looma `/v1/game/profile_sync` |
| 任务完成 | Supabase `mission_completions` | 调 looma `/v1/game/mission_complete` |
| 分享/裂变 | `getInviteUrl()` 生成 ref 参数 | 调 looma `/v1/referral/generate` |

#### 2.3 后端适配需求（给后端团队）

| 端点 | 方法 | 说明 | 前端调用方 |
|------|------|------|-----------|
| `POST /v1/auth/sync` | POST | Supabase JWT → looma token（身份桥接） | planetxStore.login() |
| `POST /v1/game/personality_result` | POST | 存储人格测试结果 + 返回分析 | planetxStore 完成测试后 |
| `GET /v1/game/profile_sync` | GET | 获取当前用户游戏状态（XP/等级/身份/任务） | planetxStore 初始化 |
| `POST /v1/game/mission_complete` | POST | 标记任务完成 + 计算 XP | planetxStore 完成任务 |
| `POST /v1/game/fleet/create` | POST | 创建舰队 | FleetPanel |
| `POST /v1/game/fleet/join` | POST | 加入舰队 | FleetPanel |
| `GET /v1/game/fleet/mine` | GET | 获取我的舰队信息 | HubScreen |
| `POST /v1/referral/generate` | POST | 生成邀请码/链接 | HubScreen 分享 |
| `GET /v1/auth/profile` | GET | 返回完整 UserProfile（含 role + tier） | authStore + planetxStore |

**验收 curl 命令**：

```bash
# 1. 身份桥接
curl -X POST https://api.genz.ltd/v1/auth/sync \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <supabase_jwt>" \
  | jq '.access_token, .user.role, .user.tier'

# 2. 人格结果提交
curl -X POST https://api.genz.ltd/v1/game/personality_result \
  -H "Authorization: Bearer <looma_token>" \
  -H "Content-Type: application/json" \
  -d '{"type":"navigator","scores":{"logic":7,"creativity":5}}' \
  | jq '.analysis, .xp_gained'

# 3. 游戏状态同步
curl -H "Authorization: Bearer <looma_token>" \
  https://api.genz.ltd/v1/game/profile_sync \
  | jq '.xp, .level, .missions_completed, .identity'

# 4. 完整用户 Profile（含 role）
curl -H "Authorization: Bearer <looma_token>" \
  https://api.genz.ltd/v1/auth/profile \
  | jq '.id, .email, .name, .role, .tier, .is_admin'
```

#### 验收标准

| 标准 | 验证 |
|------|------|
| PlanetX 注册/登录 → looma 有用户记录 | 注册后 looma `/v1/auth/profile` 能查到用户 |
| 人格测试结果在 looma 可查 | `/v1/game/profile_sync` 返回 `personality_type` |
| 同一用户 PlanetX 和 T空间身份一致 | 同 email 在两端 `/v1/auth/profile` 返回相同 `user_id` |
| 舰队数据在 looma 可查 | `/v1/game/fleet/mine` 返回舰队信息 |
| Supabase 不再存储游戏数据 | PlanetX 前端不调用 `supabase.from()` 写数据 |

---

### Phase 3：转化链路打通（3-5 天）

**目标**：C端用户自然流向 B端付费，数据驱动转化

#### 3.1 PlanetX 转化入口设计

| 位置 | UI 元素 | 功能 | 数据流向 |
|------|----------|------|----------|
| HubScreen「任务」Tab | 「🔍 星际匹配」任务 | 完成人格测试后解锁，调 `/v1/jobs/match`（简版） | looma 知道用户想做职位匹配 |
| HubScreen「我的」Tab | 「升级 Pro」按钮 | 点击跳转 `/pricing` 或内嵌支付 | tier: free → pro |
| ResultScreen | 「查看深度报告」链接 | Pro 用户可看完整人格分析 + 职业建议 | `/v1/game/personality_result` 返回详细分析 |
| ResultScreen 底部 | 「分享给猎头」按钮 | 生成分享链接，HR 可查看求职者画像 | `/v1/referral/generate` → `/v1/enterprise/candidate_view` |

#### 3.2 T空间 转化承接

| 页面 | 功能 | 数据来源 |
|------|------|----------|
| 企业管理面板 `/enterprise` | 查看/邀请/管理求职者 | `/v1/enterprise/users` |
| 求职者画像页 `/candidate/:id` | HR 查看求职者 PlanetX 报告 | `/v1/enterprise/candidate/:id` → 返回人格+匹配数据 |
| 使用统计 `/enterprise/usage` | 团队配额 + 活跃度 | `/v1/enterprise/usage` |

#### 3.3 后端适配需求

| 端点 | 方法 | 说明 |
|------|------|------|
| `GET /v1/jobs/match` | GET | 简版职位匹配（PlanetX 用），基于人格结果推荐 |
| `GET /v1/enterprise/candidate/:id` | GET | 求职者画像（HR 视角），含 PlanetX 人格+匹配报告 |
| `POST /v1/enterprise/invite` | POST | 企业邀请求职者加入 tenant |
| `GET /v1/enterprise/users` | GET | 企业 tenant 下所有用户列表 |
| `GET /v1/enterprise/usage` | GET | tenant 级配额使用统计 |

#### 验收标准

| 标准 | 验证 |
|------|------|
| PlanetX Hub 有 Pro 升级入口 | HubScreen 显示「升级 Pro」按钮，点击跳转定价页 |
| Pro 升级后深度报告可看 | tier=pro 时 ResultScreen 显示完整分析 |
| HR 能看到求职者报告 | `/v1/enterprise/candidate/:id` 返回人格数据 |
| 邀请码裂变完整 | PlanetX → 生成邀请 → 新用户注册 → 自动关联 tenant |
| DNSPod 拦截已修复 | curl GET + Bearer 无 302 重定向 |

---

### Phase 4：B端 SaaS 完整化（5-7 天）

**目标**：T空间作为独立 SaaS 产品可用

#### 4.1 saas 包功能完善

| 页面 | 当前状态 | 目标状态 |
|------|----------|----------|
| Dashboard | 有基础框架 + 配额展示 | 加转化漏斗图、团队活跃度、知识库统计 |
| Chat (RAG) | 有基础 UI | 加来源标注、引用片段、反馈评分 |
| Documents | 有上传/列表 | 加批量上传、分类标签、企业共享库 |
| Resume | 有解析 UI | 加批量解析、结构化输出、导出 PDF |
| Jobs | 有匹配 UI | 加精版匹配（基于 PlanetX 人格数据）、HR 视角 |
| Reports | 有基础 | 加模板选择、定时生成、导出 |
| Enterprise (新) | **不存在** | 企业管理面板：用户列表 + 统计 + 知识库 |
| Candidate (新) | **不存在** | 求职者画像页（HR 查看 PlanetX 报告） |

#### 4.2 后端适配需求

| 端点 | 说明 | 优先级 |
|------|------|--------|
| `/v1/enterprise/*` 全套 | 企业 CRUD + 统计 + 知识库 | P0 |
| `/v1/auth/profile` 返回 `role` | 区分 job_seeker / admin / enterprise_admin | P0 |
| `/v1/documents` 支持企业共享 | tenant schema 文档可见性 | P1 |
| `/v1/reports/template` | 报告模板选择 | P2 |

#### 验收标准

| 标准 | 验证 |
|------|------|
| 企业管理员可登录 T空间 | enterprise_admin role → Dashboard 显示企业视角 |
| 企业管理员可邀请用户 | `/v1/enterprise/invite` → 新用户自动加入 tenant |
| 企业管理员可见求职者画像 | `/enterprise/candidates` 页面显示 PlanetX 报告 |
| SaaS 独立部署 | `app.genz.ltd` 不依赖 PlanetX 前端代码 |

---

## 四、优先级排序与里程碑

```
Week 1:  Phase 0 (产品边界确认) + Phase 1 启动 (拆包)
Week 2:  Phase 1 完成 (独立 build/dev) + Phase 2 启动 (认证统一)
Week 3:  Phase 2 完成 (游戏数据回归 looma)
Week 4:  Phase 3 (转化链路) + Phase 4 启动 (B端 SaaS)
Week 5-6: Phase 4 完成 (企业管理面板 + 求职者画像)
```

| 里程碑 | 时间 | 交付物 | 依赖 |
|--------|------|--------|------|
| M0 边界确认 | Day 1 | 产品边界文档 + API 路由分区文档 | 团队共识 |
| M1 拆包完成 | Day 5 | planetx + saas 独立 build/dev | M0 |
| M2 认证统一 | Day 12 | PlanetX 数据走 looma API | 后端 `/v1/game/*` + `/v1/auth/sync` |
| M3 转化链路 | Day 17 | Pro 升级入口 + 裂变 + HR 画像 | 后端 `/v1/enterprise/*` + DNSPod 修复 |
| M4 SaaS 完整 | Day 24 | 企业管理面板可用 | 后端 enterprise 路由组完整 |

---

## 五、给后端团队的 API 路由分区文档

### 5.1 路由分组

| 路由组 | 服务对象 | 现有端点 | 需新增端点 |
|--------|---------|----------|-----------|
| `/v1/auth/*` | 通用（C+B） | login, register, refresh, quota | **sync** (JWT 桥接), **profile** (含 role) |
| `/v1/game/*` | C端 PlanetX | **无** | profile_sync, personality_result, mission_complete, fleet/* |
| `/v1/ask` | 通用 | ✅ 已有 | 无 |
| `/v1/jobs/*` | 通用 | ✅ 已有 | match (基于人格的简版) |
| `/v1/resume/*` | B端 | ✅ 已有 | 无 |
| `/v1/reports/*` | B端 | ✅ 已有 | 无 |
| `/v1/documents/*` | B端 | ✅ 已有 | tenant 可见性 |
| `/v1/referral/*` | C端 | ✅ 已有 | generate (生成邀请码) |
| `/v1/enterprise/*` | B端 T空间 | **无** | users, invite, remove, usage, candidate/:id |
| `/v1/quota` | 通用 | ✅ 已有 | 无 |

### 5.2 关键契约修正

| 端点 | 现在返回 | 应返回 | 影响 |
|------|----------|--------|------|
| `POST /v1/auth/login` | `{access_token, user_id, tier}` | `{access_token, user: {id, email, name, role, tier}}` | 前端 login 后不再需要额外调 profile |
| `POST /v1/auth/register` | `{access_token, user_id}` | `{access_token, user: {id, email, name, role}}` | 同上 |
| `GET /v1/auth/profile` | **不存在** | `{id, email, name, role, tier, is_admin, created_at}` | AuthGuard + planetxStore 初始化 |
| `POST /v1/auth/sync` | **不存在** | `{access_token, user: {...}}` | PlanetX Supabase JWT → looma 身份桥接 |

### 5.3 DNSPod 拦截修复需求

**问题**: GET 请求带 `Authorization: Bearer xxx` 头 → 被 DNSPod 安全策略 302 重定向到 `dnspod.qcloud.com/static/webblock.html`

**排查方向**:
1. 检查 Cloudflare WAF 规则是否拦截带特定 header 的 GET 请求
2. 检查腾讯云 DNSPod 的安全防护策略配置
3. 确认 `api.genz.ltd` 域名备案状态是否正常
4. 测试：`curl -H "Authorization: Bearer test" https://api.genz.ltd/v1/auth/profile` 应返回 401/403 而非 302

**验收**: `curl -v -H "Authorization: Bearer <valid_token>" https://api.genz.ltd/v1/auth/profile` 无 302 重定向

---

## 六、风险与对策

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| 后端 `/v1/game/*` 开发延期 | 中 | PlanetX 数据继续存在 Supabase | Phase 2 前先用 looma mock API，planetxStore 加 mock 模式 |
| DNSPod 拦截短期无法修复 | 中 | 国内用户 GET+Bearer 不通 | Phase 2 后所有 GET 改为 POST（后端适配），或加 CDN 白名单 |
| 拆包导致 shared 包依赖膨胀 | 低 | 两个包引入不需要的代码 | shared 拆为 `core` + `planetx-types` + `saas-types` |
| 团队对边界文档有分歧 | 中 | Phase 1 开始方向不清 | Phase 0 必须全员签字确认，不确认不推进 |
| Supabase 服务不稳定 | 低 | PlanetX 注册/登录挂 | 备选：looma 自建 auth（Phase 2 后期可选） |

---

## 七、附录：文件迁移清单（Phase 1 执行参考）

### 从 `packages/web` → `packages/planetx`

| 文件 | 新位置 | 说明 |
|------|--------|------|
| `src/pages/planetx/*` (7 files) | `planetx/src/pages/*` | 全部迁移 |
| `src/components/planetx/*` (6 files) | `planetx/src/components/*` | StarBackground, ToastBar, AchievementPopup, XPBar, FleetPanel, SharePanel |
| `src/stores/planetxStore.ts` | `planetx/src/stores/planetxStore.ts` | 改为调 looma API |
| `src/types/planetx/*` | `planetx/src/types/*` | Identity, PersonalityType 等 |
| CSS: 暗色主题相关 | `planetx/src/styles/` | bg-[#080810] 系列样式 |

### 从 `packages/web` → `packages/saas`（原地重构）

| 操作 | 说明 |
|------|------|
| 删除 `src/pages/planetx/*` | PlanetX 代码全部移走 |
| 删除 `src/components/planetx/*` | PlanetX 组件全部移走 |
| 删除 `src/stores/planetxStore.ts` | 不再需要 |
| 删除 `src/types/planetx/*` | 不再需要 |
| `App.tsx` 移除 `/planetx` 路由 | 只保留 auth + panel 路由 |
| 新增 `src/pages/enterprise/*` | 企业管理面板 |
| 新增 `src/pages/candidate/*` | 求职者画像页 |
| `package.json` name → `@looma/saas` | 包名变更 |

### `@looma/shared` 新增

| 文件 | 说明 |
|------|------|
| `api/planetx.ts` | `createPlanetXApi()` — game + referral + ask |
| `api/saas.ts` | `createSaasApi()` — enterprise + auth/profile + quota |
| `types/planetx.ts` | PlanetXUser, GameProfile, PersonalityResult, Fleet 等 |
| `types/saas.ts` | SaasUser, Enterprise, CandidateProfile 等 |
| `constants/planetx.ts` | BRAND_PLANETX, SUPABASE_URL, XP_TABLE 等 |
| `constants/saas.ts` | BRAND_SAAS, NAV_ITEMS_SAAS 等 |

---

> **下一步**: 先完成 Phase 0（产品边界确认），团队签字后再开始 Phase 1 拆包。
> 本文档随开发推进持续更新。
