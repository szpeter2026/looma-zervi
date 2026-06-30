# PlanetX 小程序端适配与重构方案

> **版本**: v1.0 | **日期**: 2026-06-29 | **分支**: `refactor/framework-v2`
> **决策方**: Peter | **状态**: 待确认

---

## 1. 项目背景与目标

### 1.1 为什么选择小程序作为内测主攻方向

- **微信生态获客成本低**: 12亿月活用户，分享裂变天然适合
- **用户教育门槛低**: 无需安装，扫码即用，适合快速验证产品假设
- **内测反馈闭环短**: 小程序版本更新即时生效，不需要用户手动更新
- **与 PlanetX Web 端互补**: Web 端做 SEO 获客，小程序做转化和留存

### 1.2 当前状态

| 维度 | 现状 | 目标 |
|------|------|------|
| 页面数 | 2 个（index + auth） | 10+ 个（TabBar 3 + 跳转 7+） |
| 代码行数 | ~474 行 | ~3000-4000 行 |
| 功能 | 仅登录 + 邮箱绑定 | 完整 C 端产品功能 |
| shared-core 复用 | 无 | types/constants 100% 复用 |
| 品牌组件 | 无 | XPBar/星空背景/成就弹窗等 |
| appid | 占位符 | CloudBase 环境 |
| 状态管理 | globalData + setTimeout 轮询 | 事件总线 + 页面 setData |

### 1.3 重构目标

1. **功能完整**: 覆盖 PlanetX Web 端核心功能（人格测试/任务/舰队/AI问答）
2. **体验一致**: 星空主题品牌视觉，与 Web 端保持统一调性
3. **代码复用**: 最大化复用 shared-core 类型定义和工具函数
4. **工程规范**: TypeScript + 组件化 + 事件驱动状态管理

---

## 2. 架构设计

### 2.1 整体架构

```
微信小程序 (原生 TypeScript)
    |
    |-- wx.login() → code
    |-- POST /v1/auth/wechat {code} → looma 后端
    |-- looma 后端 → 微信API换 openid → 签发 JWT
    |
    ↓ (Bearer JWT)
    ↓
Looma Flask 后端 (api.genz.ltd)
    |-- /v1/auth/*     认证
    |-- /v1/ask        AI 问答
    |-- /v1/game/*     游戏化（人格/任务/舰队）
    |-- /v1/quota      配额
    |-- /v1/jobs/*     职位匹配
    |-- /v1/resume/*   简历解析
    |-- /v1/referral/* 邀请码
```

### 2.2 CloudBase 定位

CloudBase 在本项目中承担**轻量接入层**角色，不做核心后端：

| CloudBase 能力 | 是否使用 | 说明 |
|----------------|---------|------|
| 小程序 appid | **是** | 通过云开发环境获取小程序 appid |
| 云函数 | **可选（P1）** | 可作为 API 代理隐藏后端地址，P0 不用 |
| 云数据库 | **否** | 核心数据在 looma 后端（SQLite + ChromaDB） |
| 云存储 | **可选** | 用户头像等静态资源，P1 考虑 |
| 微信支付连接器 | **P2** | Pro 付费上线时升级标准版（199元/月） |

**认证流程**（P0 方案，直接调 looma 后端）：

```
小程序启动
  ↓
wx.login() → 获取 code
  ↓
POST https://api.genz.ltd/v1/auth/wechat { code }
  ↓
looma 后端 → code2session(code) → 微信API换 openid
  ↓
looma 后端 → 查找/创建用户 → 签发 JWT
  ↓
小程序缓存 JWT → 后续请求带 Authorization: Bearer <token>
```

> **注意**: looma 后端的 `WECHAT_APPID` 和 `WECHAT_APP_SECRET` 需要配置为 CloudBase 小程序对应的 appid 和 secret。

### 2.3 为什么不用 CloudBase 云函数做 API 代理

P0 阶段不使用云函数代理，理由：

1. **增加延迟**: 请求多跳一跳（小程序 → 云函数 → looma 后端）
2. **增加维护成本**: 需要维护云函数代码和部署流程
3. **后端已有 CORS**: looma 后端已支持跨域请求
4. **域名白名单足够**: 小程序 request 合法域名配置 `api.genz.ltd` 即可

如果后续需要隐藏后端地址或做请求聚合，P1 阶段可以引入云函数代理。

---

## 3. 技术选型

### 3.1 框架: 纯原生微信小程序

| 方案 | 优势 | 劣势 | 决策 |
|------|------|------|------|
| **纯原生** | 性能最优、调试直接、无框架开销 | 无法跨端 | **选择** |
| Taro 4 | 跨端（RN/H5）、React 语法 | 编译复杂、包体大、调试链路长 | 否 |
| uni-app | 跨端、Vue 语法 | 小程序兼容性坑多 | 否 |

理由：小程序是唯一目标平台，不需要跨端。原生开发性能最优，且当前代码已是原生 .ts 结构。

### 3.2 状态管理: 事件总线 + globalData

不引入 mobx-miniprogram 等第三方库，自建轻量事件总线：

```typescript
// utils/eventBus.ts
type EventHandler = (data?: any) => void;
const listeners: Record<string, EventHandler[]> = {};

export function on(event: string, handler: EventHandler) { ... }
export function off(event: string, handler: EventHandler) { ... }
export function emit(event: string, data?: any) { ... }

// 事件清单
export const EVENTS = {
  LOGIN_SUCCESS: "login:success",
  LOGIN_FAILED: "login:failed",
  TOKEN_EXPIRED: "auth:token_expired",
  XP_UPDATED: "game:xp_updated",
  MISSION_COMPLETED: "game:mission_completed",
  PROFILE_UPDATED: "auth:profile_updated",
} as const;
```

**替代当前 setTimeout 轮询方案**：
```
app.ts wechatLogin() 成功 → emit(LOGIN_SUCCESS)
首页 onShow() → on(LOGIN_SUCCESS, handler) → 更新 UI
```

### 3.3 TypeScript 配置

创建 `tsconfig.json`，启用严格类型检查：

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "CommonJS",
    "strict": true,
    "noImplicitAny": true,
    "moduleResolution": "node",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "lib": ["ES2020"],
    "types": ["miniprogram-api-typings"]
  },
  "include": ["./**/*.ts"],
  "exclude": ["node_modules"]
}
```

需要安装 `miniprogram-api-typings` 提供 `wx.*` API 类型定义。

---

## 4. shared-core 复用策略

### 4.1 复用矩阵

| shared-core 模块 | 复用率 | 复用方式 | 说明 |
|------------------|--------|---------|------|
| `types/auth.ts` | 100% | 直接引用 | User/Profile/AuthResponse 等 |
| `types/chat.ts` | 100% | 直接引用 | AskRequest/AskResponse 等 |
| `types/game.ts` | 100% | 直接引用 | GameProfile/Fleet/Quiz 等 |
| `types/resume.ts` | 100% | 直接引用 | ParsedResume/Job/JobMatch 等 |
| `types/enterprise.ts` | 100% | 直接引用 | Enterprise（P2） |
| `types/brand.ts` | 100% | 直接引用 | BrandConfig |
| `types/common.ts` | 100% | 直接引用 | ApiResponse/Pagination |
| `constants/routes.ts` | 100% | 直接引用 | API_ROUTES |
| `constants/quota.ts` | 100% | 直接引用 | QUOTA_LIMITS |
| `utils/format.ts` | 95% | 直接引用 | formatDate 等（Intl 支持） |
| `utils/validation.ts` | 100% | 直接引用 | isValidEmail 等 |
| `api/ApiClient.ts` | 0% | 重新实现 | fetch → wx.request，但接口对齐 |
| `api/createApi.ts` | 80% | 参考实现 | 接口定义对齐，底层换 wx.request |

### 4.2 类型同步方案

小程序不支持 pnpm workspace 包引用，采用**构建时同步**方案：

```
miniprogram/
  types/           ← 从 shared-core/src/types/ 同步（构建脚本）
  constants/       ← 从 shared-core/src/constants/ 同步
  utils/
    format.ts      ← 从 shared-core/src/utils/format.ts 同步
    validation.ts  ← 从 shared-core/src/utils/validation.ts 同步
    api.ts         ← 小程序专用 API 封装（基于 wx.request）
    eventBus.ts    ← 小程序专用事件总线
```

同步脚本（P0 实现）：
```bash
# scripts/sync-shared-core.sh
# 从 shared-core 同步类型定义和工具函数到 miniprogram
cp ../shared-core/src/types/*.ts miniprogram/types/
cp ../shared-core/src/constants/*.ts miniprogram/constants/
cp ../shared-core/src/utils/format.ts miniprogram/utils/format.ts
cp ../shared-core/src/utils/validation.ts miniprogram/utils/validation.ts
```

### 4.3 API 层适配

小程序专用 API 封装，接口对齐 shared-core 的 `createApi`：

```typescript
// utils/api.ts (重构后)
import { API_ROUTES } from "../constants/routes";

// 基于 wx.request 的 HTTP 客户端
export class MiniApiClient {
  private baseUrl: string;
  private getToken: () => string | null;

  constructor(baseUrl: string, getToken: () => string | null) {
    this.baseUrl = baseUrl;
    this.getToken = getToken;
  }

  async get<T>(path: string): Promise<T> { ... }
  async post<T>(path: string, data?: any): Promise<T> { ... }
  async put<T>(path: string, data?: any): Promise<T> { ... }
  async delete<T>(path: string): Promise<T> { ... }
}

// API 工厂函数（对齐 shared-core createApi）
export function createMiniApi(client: MiniApiClient) {
  return {
    auth: {
      wechat: (code: string) => client.post(API_ROUTES.AUTH.WECHAT, { code }),
      profile: () => client.get(API_ROUTES.AUTH.PROFILE),
      refresh: () => client.post(API_ROUTES.AUTH.REFRESH),
      bind: (code: string) => client.post(API_ROUTES.AUTH.BIND, { code }),
    },
    ask: {
      ask: (req: AskRequest) => client.post(API_ROUTES.ASK, req),
      rate: (queryId: string, rating: number) =>
        client.post(API_ROUTES.FEEDBACK.RATE, { query_id: queryId, rating }),
    },
    game: {
      profile: () => client.get(API_ROUTES.GAME.PROFILE),
      profileSync: (data: ProfileSyncRequest) =>
        client.post(API_ROUTES.GAME.PROFILE_SYNC, data),
      missionComplete: (missionId: string) =>
        client.post(API_ROUTES.GAME.MISSION_COMPLETE, { mission_id: missionId }),
      createFleet: (name: string) =>
        client.post(API_ROUTES.GAME.FLEET_CREATE, { name }),
      joinFleet: (code: string) =>
        client.post(API_ROUTES.GAME.FLEET_JOIN, { code }),
      myFleet: () => client.get(API_ROUTES.GAME.FLEET_MINE),
      leaveFleet: () => client.post(API_ROUTES.GAME.FLEET_LEAVE),
    },
    quota: {
      get: () => client.get(API_ROUTES.QUOTA),
    },
    jobs: {
      list: () => client.get(API_ROUTES.JOBS.LIST),
      match: (resumeText: string) =>
        client.post(API_ROUTES.JOBS.MATCH, { resume_text: resumeText }),
    },
    resume: {
      parse: (text: string) =>
        client.post(API_ROUTES.RESUME.PARSE, { text }),
    },
    referral: {
      create: (tierGrant?: string) =>
        client.post(API_ROUTES.REFERRAL.CREATE, { tier_grant: tierGrant }),
      use: (code: string) =>
        client.post(API_ROUTES.REFERRAL.USE, { code }),
      myCodes: () => client.get(API_ROUTES.REFERRAL.MY_CODES),
    },
  };
}
```

---

## 5. 页面规划

### 5.1 TabBar 结构

```
TabBar (3 Tab)
├── Tab 1: 首页 (pages/hub/hub)       — 任务/XP/人格概览
├── Tab 2: 问答 (pages/ask/ask)       — AI 对话
└── Tab 3: 我的 (pages/profile/profile) — 个人中心
```

TabBar 图标需要准备（3 个 Tab × 2 状态 = 6 个图标）：
- `assets/tab/home.png` / `assets/tab/home-active.png`
- `assets/tab/ask.png` / `assets/tab/ask-active.png`
- `assets/tab/profile.png` / `assets/tab/profile-active.png`

### 5.2 完整页面清单

| 优先级 | 页面 | 路径 | 类型 | 对标 Web 端 | 核心 API |
|--------|------|------|------|------------|---------|
| **P0** | 启动页 | pages/splash/splash | navigateTo | LoadingScreen | POST /v1/auth/wechat |
| **P0** | 引导页 | pages/onboarding/onboarding | navigateTo | OnboardingScreen | POST /v1/game/profile-sync |
| **P0** | Hub 首页 | pages/hub/hub | TabBar | HubScreen | GET /v1/game/profile, GET /v1/quota |
| **P0** | 人格测试 | pages/quiz/quiz | navigateTo | QuizScreen | (纯前端) → POST /v1/game/profile-sync |
| **P0** | 测试结果 | pages/quiz/result | navigateTo | ResultScreen | POST /v1/game/mission-complete |
| **P1** | AI 问答 | pages/ask/ask | TabBar | (无) | POST /v1/ask |
| **P1** | 个人中心 | pages/profile/profile | TabBar | HubScreen profile tab | GET /v1/auth/profile, GET /v1/quota |
| **P1** | 舰队管理 | pages/fleet/fleet | navigateTo | HubScreen team tab | POST /v1/game/fleet/*, GET /v1/game/fleet/mine |
| **P1** | 配额详情 | pages/quota/quota | navigateTo | (无) | GET /v1/quota |
| **P2** | 简历解析 | pages/resume/parse | navigateTo | (无) | POST /v1/resume/parse |
| **P2** | 职位匹配 | pages/jobs/match | navigateTo | (无) | GET /v1/jobs/list, POST /v1/jobs/match |
| **P2** | 邀请码 | pages/referral/referral | navigateTo | (无) | /v1/referral/* |
| **P2** | 账号绑定 | pages/auth/bind | navigateTo | (无) | POST /v1/auth/bind |

### 5.3 用户流程

```
启动
  ↓
splash 页 (wx.login → JWT)
  ↓
  ├── 已有 token → 直接进 Hub 首页
  └── 无 token → wx.login → /v1/auth/wechat → JWT → Hub
  ↓
Hub 首页
  ├── 首次登录 → 引导页 (选择身份) → 回到 Hub
  ├── 点击"人格测试" → quiz 页 → result 页 → 回到 Hub
  ├── 切换到"问答" Tab → ask 页 (AI 对话)
  ├── 切换到"我的" Tab → profile 页
  │     ├── 点击"舰队" → fleet 页
  │     ├── 点击"配额" → quota 页
  │     ├── 点击"简历解析" → resume/parse 页 (P2)
  │     ├── 点击"职位匹配" → jobs/match 页 (P2)
  │     └── 点击"邀请码" → referral 页 (P2)
  └── 分享 → onShareAppMessage (好友) / onShareTimeline (朋友圈)
```

### 5.4 页面详细设计

#### P0-1: 启动页 (pages/splash/splash)

- **功能**: 微信登录 + 加载动画
- **UI**: 星空背景 + "PlanetX" Logo + "跃迁引擎预热中..." + 旋转行星动画
- **逻辑**:
  1. `onLoad`: 检查缓存 token
  2. 有 token → `GET /v1/auth/profile` 验证 → 有效则 `switchTab` 到 Hub
  3. 无 token / token 过期 → `wx.login()` → `POST /v1/auth/wechat` → 缓存 JWT → `switchTab` 到 Hub
  4. 登录失败 → 显示"网络错误，点击重试"
- **事件**: `emit(LOGIN_SUCCESS)` 或 `emit(LOGIN_FAILED)`

#### P0-2: 引导页 (pages/onboarding/onboarding)

- **功能**: 首次登录身份选择
- **UI**: 三选一卡片
  - 星际探索者（求职者）
  - 舰队舰长（组队 leader）
  - 星际漫游者（佛系体验）
- **逻辑**: 选择后 `POST /v1/game/profile-sync` 同步 identity → `+10 XP` → 返回 Hub
- **条件**: 仅 `is_early_adopter` 且未选择过 identity 时显示

#### P0-3: Hub 首页 (pages/hub/hub)

- **功能**: 主中心页，3 个区域
- **UI 布局**:
  ```
  ┌─────────────────────────┐
  │  PlanetX    [等级] [XP条] │  ← 顶部状态栏
  ├─────────────────────────┤
  │  人格概览卡片             │  ← 人格类型 + emoji + 标签
  │  (未测试 → 显示"开始测试")│
  ├─────────────────────────┤
  │  任务列表                 │  ← 4 个递进任务
  │  ✓ 人格测试              │     1. 人格测试 (+50 XP)
  │  ○ 组建舰队              │     2. 组建舰队 (+30 XP)
  │  ○ AI 问答               │     3. AI 问答 (+20 XP)
  │  ○ 分享给好友             │     4. 分享 (+20 XP)
  ├─────────────────────────┤
  │  舰队面板 (简略)          │  ← 舰队名/成员数/加入按钮
  └─────────────────────────┘
  ```
- **API**: `GET /v1/game/profile`, `GET /v1/quota`
- **事件**: 监听 `XP_UPDATED` / `MISSION_COMPLETED` 刷新 UI

#### P0-4: 人格测试 (pages/quiz/quiz)

- **功能**: 8 题人格测试
- **UI**: 进度条 + 题目 + 4 选项卡片
- **题库**: 从 shared-core 的 game types 同步（8 题 × 4 选项 × trait 权重）
- **逻辑**: 每次选择记录 trait 权重，8 题完成后计算人格类型
- **完成**: `POST /v1/game/profile-sync` (同步 personalityType) → `navigateTo` 到结果页

#### P0-5: 测试结果 (pages/quiz/result)

- **功能**: 展示人格类型 + 分享
- **UI**:
  - 人格名称 + emoji + 标签 + 描述
  - 分享预览卡片
  - "分享给好友" 按钮 → `onShareAppMessage`
  - "分享到朋友圈" 按钮 → `onShareTimeline`
  - "返回首页" 按钮 → `switchTab` 到 Hub
- **API**: `POST /v1/game/mission-complete` (完成人格测试任务 +50 XP)
- **分享**: 使用小程序原生分享能力，不需要 Canvas

#### P1-1: AI 问答 (pages/ask/ask)

- **功能**: AI 对话界面
- **UI**: 聊天消息列表 + 底部输入框 + 发送按钮
- **API**: `POST /v1/ask` (支持 navigator_mode)
- **特性**:
  - 消息气泡（用户右侧 #6C63FF，AI 左侧深色卡片）
  - 加载状态（AI 思考中...）
  - 配额提示（剩余次数）
  - 快捷问题推荐

#### P1-2: 个人中心 (pages/profile/profile)

- **功能**: 用户信息 + 功能入口
- **UI 布局**:
  ```
  ┌─────────────────────────┐
  │  [头像] 用户名            │
  │  等级 Lv.X | XP: xxx/yyy  │
  │  Tier: free [升级]       │
  ├─────────────────────────┤
  │  我的舰队          >     │  → fleet 页
  │  配额详情          >     │  → quota 页
  │  简历解析          >     │  → resume/parse 页 (P2)
  │  职位匹配          >     │  → jobs/match 页 (P2)
  │  邀请码            >     │  → referral 页 (P2)
  ├─────────────────────────┤
  │  退出登录                 │
  └─────────────────────────┘
  ```
- **API**: `GET /v1/auth/profile`, `GET /v1/quota`

#### P1-3: 舰队管理 (pages/fleet/fleet)

- **功能**: 创建/加入/离开舰队
- **API**: `POST /v1/game/fleet/create`, `POST /v1/game/fleet/join`, `GET /v1/game/fleet/mine`, `POST /v1/game/fleet/leave`
- **UI**: 
  - 无舰队：创建舰队（输入名称）/ 加入舰队（输入邀请码）
  - 有舰队：舰队名 + 成员列表 + 离开按钮

---

## 6. 品牌组件

对标 PlanetX Web 端的 8 个品牌组件，小程序端实现以下组件：

| 组件 | 路径 | 功能 | 优先级 |
|------|------|------|--------|
| star-background | components/star-background/ | 星空背景动画（CSS animation） | P0 |
| xp-bar | components/xp-bar/ | 经验值进度条 | P0 |
| achievement-popup | components/achievement-popup/ | 成就弹窗（升级/完成任务） | P0 |
| toast-bar | components/toast-bar/ | 全局提示条 | P0 |
| mission-card | components/mission-card/ | 任务卡片 | P0 |
| fleet-panel | components/fleet-panel/ | 舰队面板 | P1 |
| share-card | components/share-card/ | 分享预览卡片 | P1 |
| loading-spinner | components/loading-spinner/ | 加载动画 | P0 |

### 6.1 星空背景 (star-background)

```css
/* 使用 CSS animation 实现星星闪烁，不用 Canvas */
.star {
  position: absolute;
  width: 2rpx;
  height: 2rpx;
  background: #fff;
  border-radius: 50%;
  animation: twinkle 3s infinite;
}
@keyframes twinkle {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
```

### 6.2 品牌色值

```css
/* app.wxss 全局样式 */
page {
  --color-bg: #0a0a1a;           /* 深蓝黑背景 */
  --color-bg-card: #1a1a2e;      /* 卡片背景 */
  --color-primary: #6C63FF;       /* PlanetX 紫色 */
  --color-accent: #C8FF50;        /* 星际绿 */
  --color-text: #ffffff;          /* 白色文字 */
  --color-text-secondary: #a0a0b8; /* 次要文字 */
  --color-border: rgba(255,255,255,0.1); /* 边框 */
  
  background: var(--color-bg);
  color: var(--color-text);
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
}
```

---

## 7. 分批实施计划

### 7.1 P0: 基础设施 + 核心页面（预计 5-7 天）

#### Step 1: 基础设施搭建（1-2 天）

- [ ] 创建 `app.wxss` 全局样式（品牌色值 + 通用样式）
- [ ] 创建 `tsconfig.json` TypeScript 配置
- [ ] 安装 `miniprogram-api-typings` 类型定义
- [ ] 配置 `app.json` TabBar（3 Tab + 图标）
- [ ] 创建 `utils/eventBus.ts` 事件总线
- [ ] 创建 shared-core 同步脚本
- [ ] 同步 types/constants/utils 到 miniprogram
- [ ] 重构 `utils/api.ts` → `MiniApiClient` + `createMiniApi`
- [ ] 重构 `app.ts`（事件驱动登录流程）
- [ ] 配置 `project.config.json`（appid + 编译设置）

#### Step 2: 启动页 + 引导页（1 天）

- [ ] 创建 `pages/splash/splash` 启动页
- [ ] 创建 `pages/onboarding/onboarding` 引导页
- [ ] 实现 star-background 组件
- [ ] 实现 loading-spinner 组件

#### Step 3: Hub 首页（1-2 天）

- [ ] 创建 `pages/hub/hub` 首页
- [ ] 实现 xp-bar 组件
- [ ] 实现 mission-card 组件
- [ ] 实现 toast-bar 组件
- [ ] 对接 `GET /v1/game/profile` + `GET /v1/quota`

#### Step 4: 人格测试 + 结果（1-2 天）

- [ ] 创建 `pages/quiz/quiz` 测试页
- [ ] 创建 `pages/quiz/result` 结果页
- [ ] 同步 8 题题库 + 6 种人格类型
- [ ] 实现 achievement-popup 组件
- [ ] 对接 `POST /v1/game/profile-sync` + `POST /v1/game/mission-complete`
- [ ] 实现 `onShareAppMessage` + `onShareTimeline`

### 7.2 P1: 功能完善（预计 3-4 天）

- [ ] `pages/ask/ask` AI 问答页（对话 UI + POST /v1/ask）
- [ ] `pages/profile/profile` 个人中心
- [ ] `pages/fleet/fleet` 舰队管理
- [ ] `pages/quota/quota` 配额详情
- [ ] 实现 share-card 组件
- [ ] 实现 fleet-panel 组件

### 7.3 P2: 扩展功能（预计 2-3 天）

- [ ] `pages/resume/parse` 简历解析
- [ ] `pages/jobs/match` 职位匹配
- [ ] `pages/referral/referral` 邀请码
- [ ] `pages/auth/bind` 账号绑定

---

## 8. 配置清单

### 8.1 微信小程序配置

| 配置项 | 当前值 | 目标值 | 说明 |
|--------|--------|--------|------|
| appid | REPLACE_WITH_YOUR_APPID | CloudBase 小程序 appid | 需创建云开发环境 |
| request 合法域名 | 无 | `api.genz.ltd` | 需在小程序管理后台配置 |
 | TLS | - | 需要 HTTPS | api.genz.ltd 需配置 SSL 证书 |

### 8.2 looma 后端配置

| 环境变量 | 说明 | 来源 |
|---------|------|------|
| `WECHAT_APPID` | CloudBase 小程序 appid | CloudBase 控制台 |
| `WECHAT_APP_SECRET` | CloudBase 小程序 secret | CloudBase 控制台 |
| `JWT_SECRET` | JWT 签名密钥 | 已配置 |
| `JWT_EXPIRY_HOURS` | JWT 过期时间 | 已配置（默认 24h） |

### 8.3 小程序目录结构（重构后）

```
miniprogram/
├── app.ts                        # 入口（重构：事件驱动）
├── app.json                      # 全局配置（重构：TabBar）
├── app.wxss                      # 全局样式（新增）
├── project.config.json           # 项目配置（更新 appid）
├── sitemap.json                  # 搜索配置
├── tsconfig.json                 # TS 配置（新增）
├── types/                        # ← shared-core 同步
│   ├── auth.ts
│   ├── chat.ts
│   ├── game.ts
│   ├── resume.ts
│   ├── enterprise.ts
│   ├── brand.ts
│   └── common.ts
├── constants/                    # ← shared-core 同步
│   ├── routes.ts
│   └── quota.ts
├── utils/
│   ├── api.ts                    # 重构：MiniApiClient + createMiniApi
│   ├── eventBus.ts               # 新增：事件总线
│   ├── format.ts                 # ← shared-core 同步
│   └── validation.ts             # ← shared-core 同步
├── components/
│   ├── star-background/          # 星空背景
│   ├── xp-bar/                   # 经验值进度条
│   ├── achievement-popup/        # 成就弹窗
│   ├── toast-bar/                # 提示条
│   ├── mission-card/             # 任务卡片
│   ├── loading-spinner/          # 加载动画
│   ├── fleet-panel/              # 舰队面板 (P1)
│   └── share-card/               # 分享卡片 (P1)
├── pages/
│   ├── splash/                   # 启动页
│   ├── onboarding/               # 引导页
│   ├── hub/                      # 首页 (TabBar)
│   ├── quiz/                     # 人格测试
│   │   ├── quiz
│   │   └── result
│   ├── ask/                      # AI 问答 (TabBar, P1)
│   ├── profile/                  # 我的 (TabBar, P1)
│   ├── fleet/                    # 舰队管理 (P1)
│   ├── quota/                    # 配额详情 (P1)
│   ├── resume/                   # 简历解析 (P2)
│   ├── jobs/                     # 职位匹配 (P2)
│   ├── referral/                 # 邀请码 (P2)
│   └── auth/                     # 账号绑定 (P2)
└── assets/
    └── tab/                      # TabBar 图标
        ├── home.png
        ├── home-active.png
        ├── ask.png
        ├── ask-active.png
        ├── profile.png
        └── profile-active.png
```

---

## 9. 风险与注意事项

### 9.1 技术风险

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| api.genz.ltd 未配置 HTTPS | 高 | 小程序要求 HTTPS，需先配置 SSL 证书 |
| CloudBase 小程序 appid 未申请 | 高 | 需要先注册微信小程序 + 开通云开发 |
| 后端 WECHAT_APPID 不匹配 | 高 | 需要更新后端环境变量为 CloudBase 小程序的 appid/secret |
| shared-core 类型同步遗漏 | 中 | 同步脚本 + CI 检查（P1 引入） |
| 小程序包体积超限 | 低 | 主包 < 2MB，可按需分包加载 |
| wx.request 并发限制 | 低 | 最多 10 个并发请求，需做队列管理 |

### 9.2 体验注意事项

1. **登录体验**: 静默登录（wx.login），不要弹窗授权，用户无感
2. **加载状态**: 所有 API 请求需要显示 loading 状态
3. **错误处理**: 网络错误友好提示 + 重试按钮
4. **分享体验**: 人格测试结果页配置 `onShareAppMessage` + `onShareTimeline`
5. **TabBar 图标**: 需要 81px×81px PNG，不能用矢量图

### 9.3 与 Web 端的差异

| 功能 | Web 端 | 小程序端 | 原因 |
|------|--------|---------|------|
| 登录方式 | 邮箱/密码 | wx.login 静默登录 | 平台特性 |
| 状态管理 | Zustand | 事件总线 + globalData | 小程序无 React |
| 分享 | Canvas 导出图片 + 复制链接 | onShareAppMessage + onShareTimeline | 平台 API |
| 路由 | React Router (URL) | wx.navigateTo / wx.switchTab | 平台 API |
| 样式 | Tailwind CSS | WXSS + rpx 单位 | 平台限制 |
| SSE 流式 | fetch + ReadableStream | 不支持（改用轮询或一次性返回） | 小程序限制 |

---

## 10. 验收标准

### P0 验收

- [ ] 小程序能在微信开发者工具中正常编译运行
- [ ] 启动页 wx.login → JWT 登录流程跑通
- [ ] Hub 首页展示用户等级/XP/任务列表
- [ ] 人格测试 8 题流程完整
- [ ] 测试结果页展示人格类型 + 分享功能
- [ ] 星空背景/XPBar/成就弹窗组件正常渲染
- [ ] TypeScript 编译无错误
- [ ] shared-core 类型同步脚本可正常执行

### P1 验收

- [ ] AI 问答页对话功能正常
- [ ] 个人中心展示用户信息 + 功能入口
- [ ] 舰队创建/加入/离开功能正常
- [ ] 配额详情页展示各资源使用情况

### P2 验收

- [ ] 简历解析功能正常
- [ ] 职位匹配功能正常
- [ ] 邀请码创建/使用功能正常
- [ ] 账号绑定功能正常

---

## 附录 A: 后端 API 路由完整清单

### Auth 模块 (/v1/auth)

| 方法 | 路径 | 鉴权 | 功能 |
|------|------|------|------|
| POST | /v1/auth/register | 无 | Web 邮箱注册 |
| POST | /v1/auth/login | 无 | Web 邮箱登录 |
| POST | /v1/auth/wechat | 无 | 小程序登录 (code → JWT) |
| POST | /v1/auth/bind | require_auth | 绑定微信 openid |
| GET | /v1/auth/profile | require_auth | 获取用户资料 |
| POST | /v1/auth/refresh | require_auth | 刷新 JWT |
| POST | /v1/auth/bridge | 无 | Supabase 桥接 (MVP: 501) |

### Ask 模块 (/v1)

| 方法 | 路径 | 鉴权 | 功能 |
|------|------|------|------|
| POST | /v1/ask | optional_auth | AI 问答 |
| POST | /v1/feedback/rate | require_auth | 评分 |
| GET | /v1/feedback/last-query | require_auth | 最近查询 |

### Game 模块 (/v1/game)

| 方法 | 路径 | 鉴权 | 功能 |
|------|------|------|------|
| POST | /v1/game/profile-sync | require_auth | 同步人格结果 |
| GET | /v1/game/profile | require_auth | 游戏档案 |
| POST | /v1/game/mission-complete | require_auth | 完成任务 |
| POST | /v1/game/fleet/create | require_auth | 创建舰队 |
| POST | /v1/game/fleet/join | require_auth | 加入舰队 |
| GET | /v1/game/fleet/mine | require_auth | 我的舰队 |
| POST | /v1/game/fleet/leave | require_auth | 离开舰队 |

### 其他模块

| 方法 | 路径 | 鉴权 | 功能 |
|------|------|------|------|
| GET | /v1/quota | require_auth | 配额查询 |
| POST | /v1/resume/parse | optional_auth | 简历解析 |
| POST | /v1/resume/upload | require_auth | 简历上传 (501) |
| POST | /v1/jobs/match | optional_auth | 职位匹配 |
| GET | /v1/jobs/list | optional_auth | 职位列表 |
| POST | /v1/referral/create | require_auth | 创建邀请码 |
| POST | /v1/referral/use | require_auth | 使用邀请码 |
| GET | /v1/referral/my-codes | require_auth | 我的邀请码 |
