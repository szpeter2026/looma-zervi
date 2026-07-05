# looma-zervi UI/UX 设计外包决策文档
## 分阶段交付清单与详细数据

> 生成日期：2026-07-05  
> 最后更新：2026-07-05（Phase 3 内部交付完成 · Storybook :6007）  
> 项目：looma-zervi 前端 monorepo（PlanetX + SaaS 双品牌）  
> 决策结论：采用"纯视觉层外包 + 内部团队集成业务逻辑"的分阶段策略  
> 配套文档：[szbolent-portal-outsourcing-astra-deliverables.md](../../szbolent-portal/docs/szbolent-portal-outsourcing-astra-deliverables.md) · [PAYMENT_TIER_CONTRACT.md](../../docs/PAYMENT_TIER_CONTRACT.md) · [STORYBOOK.md](./STORYBOOK.md)
---

## 一、项目概述

### 1.1 架构背景

looma-zervi 是一个 **React + TypeScript monorepo**，包含两个独立品牌前端 + 一个共享核心层：

```
frontend/packages/
├── shared-core/     ← 契约层（API Client、类型定义、常量）
├── planetx/         ← C端 游戏化品牌（Jason 负责）
├── saas/            ← B端 企业品牌（szbenyx 负责）
└── miniprogram/     ← 微信小程序壳（统一入口）
```

### 1.2 核心设计挑战

| 挑战 | 说明 |
|------|------|
| **双品牌体系** | PlanetX（游戏化）和 SaaS（企业级）是完全不同的视觉语言，不能共用一套设计 |
| **品牌物理隔离** | `planetx` 和 `saas` 互不引用，CSS 各自独立，Design Tokens 各自独立 |
| **纯视觉层外包** | 外包方只做"皮肤"，内部团队做"血肉"——这个边界必须清晰 |
| **游戏化组件** | PlanetX 需要 XP 条、等级徽章、星空背景、动画效果——传统 SaaS 设计师不擅长 |
| **实时交互组件** | SaaS 需要聊天界面、数据看板、AI 流式输出——交互状态比普通 CRUD 复杂很多 |

---

## 二、两个品牌的页面与组件清单

### 2.1 PlanetX（C端 游戏化品牌）

```
planetx/src/
├── features/
│   ├── auth/              # 认证模块
│   │   ├── AuthScreen.tsx        # 登录/注册页
│   │   ├── LoadingScreen.tsx     # 品牌加载动画
│   │   ├── PlanetXAuthGuard.tsx  # 路由守卫（不涉及UI）
│   │   ├── planetxAuthStore.ts   # 状态管理（不涉及UI）
│   │   └── types.ts              # 类型定义
│   ├── onboarding/        # 新手引导
│   │   ├── OnboardingScreen.tsx  # 品牌故事引导页
│   │   └── NarrativeRedirect.tsx # 叙事重定向
│   ├── quiz/              # 人格测试
│   │   ├── QuizScreen.tsx        # 测试主界面
│   │   └── types.ts
│   ├── result/            # 人格结果
│   │   └── ResultScreen.tsx      # 结果展示页
│   ├── hub/               # 舰队中心
│   │   └── HubScreen.tsx         # 舰队/任务/成就中心
│   ├── tspace/            # T空间
│   │   └── TspaceNavigatorScreen.tsx  # 游戏化预演导航
│   ├── feedback/          # 反馈
│   │   └── FeedbackSurvey.tsx    # 反馈问卷
│   └── PlanetXHome.tsx    # 首页入口
├── brand/
│   ├── tokens.css         # Design Tokens（已扩展 ≥163 变量）
│   ├── animations.css     # 12 种关键帧 + 工具类
│   ├── ANIMATION_SPEC.md  # 动画规格书
│   └── ui/                # 10 个纯 UI 组件 + stories/├── styles/
│   └── globals.css        # 全局样式
└── App.tsx                # 路由入口
```

**PlanetX 页面/界面清单**：

| 序号 | 页面名称 | 源文件 | 复杂度 | 核心交互 |
|------|---------|--------|--------|---------|
| P1 | 认证页面 | AuthScreen.tsx | ★★★ | 登录/注册表单、微信扫码、Supabase 集成 |
| P2 | 加载动画 | LoadingScreen.tsx | ★★ | 品牌 loading 动画、logo 展示 |
| P3 | 新手引导 | OnboardingScreen.tsx | ★★★★★ | 品牌故事叙事、角色选择、动画过渡 |
| P4 | 叙事重定向 | NarrativeRedirect.tsx | ★★ | 过渡页 |
| P5 | 人格测试 | QuizScreen.tsx | ★★★★★ | 题目卡片、选项交互、进度动画、过渡效果 |
| P6 | 人格结果 | ResultScreen.tsx | ★★★★★ | 类型徽章、XP 条、等级、分享卡片 |
| P7 | 舰队中心 | HubScreen.tsx | ★★★★ | 舰队列表、任务卡片、成就系统 |
| P8 | T空间导航 | TspaceNavigatorScreen.tsx | ★★★★★ | 游戏化导航、场景切换 |
| P9 | 反馈问卷 | FeedbackSurvey.tsx | ★★ | 评分、文本输入 |
| P10 | 首页 | PlanetXHome.tsx | ★★★ | 品牌入口、CTA |

**PlanetX 纯 UI 组件（`brand/ui/`，10 个）**：

| 组件 | 源文件 | 关键参数 |
|------|--------|---------|
| PlanetXButton | `PlanetXButton.tsx` | primary/accent/outline/ghost/danger |
| PlanetXCard | `PlanetXCard.tsx` | 默认 / highlighted |
| PlanetXInput / TextArea | `PlanetXInput.tsx` 等 | 七态 + error |
| PlanetXXPBar | `PlanetXXPBar.tsx` | level / xp / rankName |
| PlanetXLevelBadge | `PlanetXLevelBadge.tsx` | 圆形/六边形 · tier 发光 |
| PlanetXQuizOptionCard | `PlanetXQuizOptionCard.tsx` | 选中/正确/错误 |
| PlanetXAchievementPopup | `PlanetXAchievementPopup.tsx` | claimPulse |
| PlanetXToastBar | `PlanetXToastBar.tsx` | success/error 等 |
| PlanetXLoading | `PlanetXLoading.tsx` | xSpin |
| PlanetXStarBackground | `PlanetXStarBackground.tsx` | canvas 星空 |

> 业务页组件（FleetCard、MissionCard 等）仍在 `features/`，**不在 Phase 3 纯 UI 外包范围**。
---

### 2.2 SaaS（B端 企业品牌）

```
saas/src/
├── features/
│   ├── auth/              # 认证模块
│   │   ├── Login.tsx            # 登录页
│   │   ├── Register.tsx         # 注册页
│   │   ├── SaasAuthGuard.tsx    # 路由守卫（不涉及UI）
│   │   └── authStore.ts         # 状态管理（不涉及UI）
│   ├── dashboard/         # 数据看板
│   │   └── Dashboard.tsx        # 核心看板
│   ├── chat/              # AI 聊天
│   │   ├── Chat.tsx             # 聊天界面
│   │   └── useChat.ts           # 聊天逻辑（不涉及UI）
│   ├── poetry/            # 诗词阅读
│   │   └── Poetry.tsx           # 诗词阅读器
│   ├── candidates/        # 候选人管理
│   │   ├── Candidates.tsx       # 候选人列表
│   │   ├── CandidateDetail.tsx  # 候选人详情
│   │   ├── CandidateShare.tsx   # 分享页
│   │   └── personalityDetail.ts # 人格详情组件
│   ├── hr/                # HR 模块
│   │   ├── Jobs.tsx             # 职位管理
│   │   └── Resume.tsx           # 简历管理
│   ├── pricing/           # 定价
│   │   └── Pricing.tsx          # 定价方案页
│   ├── reports/           # 报告
│   │   └── Reports.tsx          # 报告中心
│   └── settings/          # 设置
│       └── ConsentSettings.tsx  # 隐私同意管理
├── brand/
│   ├── tokens.css         # Design Tokens（已扩展 ≥216 变量）
│   ├── markdown.css       # Markdown 渲染样式
│   └── ui/                # 12 个纯 UI 组件 + stories/├── styles/
│   └── globals.css        # 全局样式
└── App.tsx                # 路由入口
```

**SaaS 页面/界面清单**：

| 序号 | 页面名称 | 源文件 | 复杂度 | 核心交互 |
|------|---------|--------|--------|---------|
| S1 | 登录页 | Login.tsx | ★★★ | 邮箱/密码登录表单、验证提示 |
| S2 | 注册页 | Register.tsx | ★★★ | 注册表单、邀请码 |
| S3 | 数据看板 | Dashboard.tsx | ★★★★★ | KPI 卡片、图表、数据统计 |
| S4 | AI 聊天 | Chat.tsx | ★★★★★ | 消息气泡、流式输出、打字动画、附件 |
| S5 | 诗词阅读 | Poetry.tsx | ★★★★ | 诗词卡片、注释弹出、收藏 |
| S6 | 候选人列表 | Candidates.tsx | ★★★★ | 列表、筛选、排序、状态标签 |
| S7 | 候选人详情 | CandidateDetail.tsx | ★★★★★ | 人格图表、简历预览、联系操作 |
| S8 | 候选人分享 | CandidateShare.tsx | ★★ | 分享卡片预览 |
| S9 | 职位管理 | Jobs.tsx | ★★★ | 职位 CRUD 列表、筛选 |
| S10 | 简历管理 | Resume.tsx | ★★★★ | 简历上传、解析预览、评分 |
| S11 | 定价方案 | Pricing.tsx | ★★ | 价格卡片、对比 |
| S12 | 报告中心 | Reports.tsx | ★★★★ | 报告列表、生成状态、下载 |
| S13 | 隐私设置 | ConsentSettings.tsx | ★★ | 同意开关、设置保存 |
| S14 | 404 页面 | （路由配置） | ★★ | 错误提示 |

**SaaS 纯 UI 组件（`brand/ui/`，12 个）**：

| 组件 | 源文件 | 用途 |
|------|--------|------|
| SaasButton | `SaasButton.tsx` | 4 变体 × 3 尺寸 |
| SaasInput / Select / TextArea | 各 `Saas*.tsx` | 表单七态 |
| SaasCard | `SaasCard.tsx` | 卡片 hoverable |
| SaasSidebar | `SaasSidebar.tsx` | 240px 侧栏 |
| SaasHeader | `SaasHeader.tsx` | 56px 顶栏 |
| SaasKPICard | `SaasKPICard.tsx` | KPI + sparkline |
| SaasDataTable | `SaasDataTable.tsx` | 表格 |
| SaasChatBubble | `SaasChatBubble.tsx` | 用户/AI + markdown |
| SaasStreamingText | `SaasStreamingText.tsx` | 流式打字 |
| SaasResumeUploader | `SaasResumeUploader.tsx` | 上传四态 |
| SaasLoading / SaasSkeleton | 各文件 | 加载/骨架 |
| SaasEmptyState / SaasErrorState | 各文件 | 空/错态 |

> AppLayout 等业务布局仍在 `features/`；Pricing 页业务逻辑接 Looma API（见 `PAYMENT_TIER_CONTRACT.md`），**不在外包纯 UI 包内**。
---

## 三、Design Tokens 与动画（Phase 3 已落地）

### 3.1 PlanetX Design Tokens（✅ 已扩展）

| 类别 | 变量前缀 | 目标 | **当前** |
|------|---------|------|----------|
| 主色 / 强调 / 语义 / 背景 / 文字 | `--px-*` | ≥80 | **163 个**（`planetx/src/brand/tokens.css`） |
| 组件级 Token | button/input/card/badge 等 | 全覆盖 | ✅ |

### 3.2 PlanetX 动画（✅ 12 keyframes）

| 交付 | 说明 |
|------|------|
| `animations.css` | 12 个 `@keyframes` + `px-anim-*` 工具类 |
| `ANIMATION_SPEC.md` | 缓动、时长、触发条件规格书 |

原 5 种基础动画已扩展为 12 种（含 xSpin、screenIn、claimPulse、fadeIn、bounceIn、numberRoll 等）。

### 3.3 SaaS Design Tokens（✅ 已扩展）

| 类别 | 变量前缀 | 目标 | **当前** |
|------|---------|------|----------|
| 主色 / 语义 / 背景 / 文字 / 布局 | `--color-*` 等 | ≥100 | **216 个**（`saas/src/brand/tokens.css`） |
| Markdown | `.markdown-body` | 8 种元素 | ✅ `markdown.css` |

### 3.4 SaaS Markdown 渲染规范（✅）

| 元素 | 样式 |
|------|------|
| 标题 h1-h3 | 1.5rem / 1.25rem / 1.1rem, font-weight: 600 |
| 行内代码 | `#f8f9fa` 背景, 2px 6px padding, SF Mono 字体 |
| 代码块 | `#1e1e1e` 深色背景, `#d4d4d4` 文字 |
| 表格 | 边框 `#e0e0e0`, 8px 12px padding |
| 引用块 | 左边框 3px `--color-primary`, padding-left 1rem |

> ⚠️ **后续扩展约定**：新增 Token 须保持 `--px-*` / `--color-*` 命名前缀；变更需同步 Storybook 预览与 `pnpm typecheck`。

---

## 四、UI 元素总量统计（两个品牌合计）

### 4.1 PlanetX 品牌

| 分类 | 数量 |
|------|------|
| 页面/界面 | 10 |
| 纯 UI 组件（`brand/ui/`） | 10 |
| Design Token 变量 | **163** |
| 关键帧动画 | **12** |
| 核心用户流程 | 3（新手引导→测试→结果 / 舰队中心 / T空间导航） |
### 4.2 SaaS 品牌

| 分类 | 数量 |
|------|------|
| 页面/界面 | 14 |
| 纯 UI 组件（`brand/ui/`） | 12 |
| Design Token 变量 | **216** |
| Markdown 渲染规范 | 1 套（8 种元素） |
| 核心用户流程 | 4（登录→看板→聊天 / 候选人管理 / 简历上传解析 / 诗词阅读） |
### 4.3 合计

| 分类 | 数量 |
|------|------|
| **页面/界面总数** | 24 |
| **纯 UI 组件** | 22 |
| **Design Token 变量** | **379**（PlanetX 163 + SaaS 216） |
| **关键帧动画** | **12** || **Markdown 渲染规范** | 1 套（覆盖 8 种元素） |
| **核心用户流程** | 7 |
| **Figma 设计稿（3 断点）** | 24 页 × 3 = 72 张 |
| **组件七态覆盖** | 22 组件 × 7 状态 = 154 个状态设计 |

---

## 五、外包边界——什么外包、什么不外包

### 5.1 外包方负责（纯视觉层）

| 交付层级 | 内容 |
|---------|------|
| **Design Tokens 扩展** | 基于现有 Token 体系，扩展完整的组件级 CSS 变量 |
| **Figma 组件库** | 22 个品牌组件的设计稿（含所有变体和七态） |
| **页面设计稿** | 24 个页面 × 3 断点 = 72 张高保真设计稿 |
| **动画规格书** | PlanetX 动画的缓动函数、时长、触发条件、视觉参考 |
| **纯 UI 组件源码** | 22 个组件的 React 代码（只含 JSX + CSS，不做数据绑定） |
| **Storybook 文档** | 每个组件含 Props 说明、变体演示 |

### 5.2 内部团队负责（业务逻辑层）

| 不做的事情 | 原因 |
|-----------|------|
| ❌ API 调用封装 | 涉及 JWT 认证、错误处理、重试逻辑 |
| ❌ 状态管理（Store） | authStore、quizStore、chatStore 等 |
| ❌ 路由守卫（AuthGuard） | PlanetX 用 Supabase bridge，SaaS 用 looma token |
| ❌ 数据流绑定 | 组件 Props 由外包方定义类型，内部团队填数据 |
| ❌ 后端交互 | API Client 封装、流式输出（SSE）、文件上传 |
| ❌ 认证逻辑 | JWT 刷新、WeChat openid、Supabase bridge |
| ❌ 小程序 | WeChat miniprogram 由内部团队独立开发 |

### 5.3 协作模式

```
                  外包方交付                    内部团队集成
                  ──────────                    ──────────
                  tokens.css  ──────────→  planetx/brand/tokens.css
              animations.css  ──────────→  planetx/brand/animations.css
         planetx/brand/ui/*.tsx ───────→  已入库 · stories 在 ui/stories/
                      ...                         内部 features/ 做数据绑定

         saas/brand/ui/*.tsx  ──────────→  已入库 · stories 在 ui/stories/
                      ...                         Pricing 接 Looma API（内部）```

---

## 六、UX 交互状态统计

### 6.1 PlanetX 品牌特有交互

| 交互类型 | 涉及页面/组件 | 说明 |
|---------|-------------|------|
| **游戏化进度** | QuizScreen, ResultScreen | 测试进度条、XP 累积动画 |
| **粒子背景** | StarBackground (全局) | canvas 星空粒子实时渲染 |
| **关卡过渡** | OnboardingScreen, TspaceNavigatorScreen | 场景切换动画 |
| **成就弹出** | AchievementPopup | claimPulse 脉冲 + 弹出 |
| **等级变化** | LevelBadge, XPBar | 升级动画、数字滚动 |
| **答题反馈** | QuizOptionCard | 选中/正确/错误三态动画 |
| **分享卡片生成** | ResultScreen | Canvas/SVG 生成分享图 |

### 6.2 SaaS 品牌特有交互

| 交互类型 | 涉及页面/组件 | 说明 |
|---------|-------------|------|
| **流式输出** | Chat, StreamingText | 逐字输出 + 光标闪烁 |
| **Markdown 渲染** | ChatBubble (AI 消息) | 代码块语法高亮、表格、引用 |
| **文件上传** | ResumeUploader | 拖拽、进度条、格式校验、预览 |
| **数据看板** | Dashboard | 图表加载、数据刷新、KPI 动画 |
| **侧边栏折叠** | Sidebar | 折叠/展开动画、子菜单 |
| **简历解析状态** | Resume | 上传中 → 解析中 → 完成/失败 |
| **个人信息脱敏** | CandidateDetail | 敏感信息遮罩、展开查看 |

### 6.3 全品牌通用交互状态

| 交互类型 | 出现频次 | 
|---------|---------|
| **Hover 悬浮效果** | 60+ 处 |
| **Loading 加载态** | 15+ 处（spinner / skeleton / streaming） |
| **Empty 空状态** | 10+ 处 |
| **Error 错误态** | 10+ 处 |
| **Success 成功态** | 5+ 处 |
| **Disabled 态** | 20+ 处 |
| **Focus 态** | 15+ 处 |
| **表单验证** | 6 组（登录/注册/反馈/简历上传/候选人筛选/职位管理） |

---

## 七、响应式设计断点与尺寸规范

### 7.1 断点方案（两个品牌相同）

| 断点 | 宽度范围 | 适用设备 |
|------|---------|---------|
| Mobile | 320px - 767px | 手机（微信内置浏览器重点适配） |
| Tablet | 768px - 1023px | 平板 |
| Desktop | 1024px+ | 笔记本/台式机（主要使用场景） |

> ⚠️ PlanetX 的移动端比例预计 >60%（微信引流入口），SaaS 的桌面端比例 >80%（B端办公场景）。

### 7.2 PlanetX 品牌尺寸规范（游戏化）

| 元素 | Desktop | Tablet | Mobile |
|------|---------|--------|--------|
| 容器最大宽度 | 480px（移动端卡片式） | 720px | 100% - 32px |
| Hero 标题字体 | 2.5rem | 2rem | 1.75rem |
| 卡片标题 | 1.5rem | 1.25rem | 1.125rem |
| 正文 | 1.125rem | 1rem | 0.9375rem |
| Card 内边距 | 32px | 24px | 20px |
| Card 间距 | 24px | 20px | 16px |
| 圆角（卡片） | 20px | 16px | 12px |
| 圆角（按钮） | 12px | 10px | 8px |
| XPBar 高度 | 8px | 8px | 6px |
| 徽章尺寸 | 80px | 64px | 56px |

### 7.3 SaaS 品牌尺寸规范（企业级）

| 元素 | Desktop | Tablet | Mobile |
|------|---------|--------|--------|
| Sidebar 宽度 | 240px | 折叠为图标 | 底部导航/汉堡菜单 |
| Header 高度 | 56px | 56px | 48px |
| 内容区最大宽度 | 1200px | 100% | 100% |
| 表格/卡片标题 | 1.25rem | 1.125rem | 1rem |
| 正文 | 0.9375rem | 0.875rem | 0.875rem |
| Card 内边距 | 24px | 20px | 16px |
| Card 间距 | 24px | 20px | 16px |
| 圆角（卡片/表格） | 8px | 8px | 6px |
| 圆角（按钮） | 6px | 6px | 6px |
| 侧边栏字号 | 0.875rem | 图标 | 图标 |

---

## 八、分阶段交付清单

### Phase 1：品牌基调确认 + Design Tokens 扩展（2-3 周，15% 款项）

| 交付物 | 量化指标 | 说明 |
|--------|---------|------|
| PlanetX 品牌情绪板 | 2 套方案 | 星际/深空/赛博朋克 方向探索 |
| SaaS 品牌情绪板 | 2 套方案 | 专业/现代/极简 方向探索 |
| PlanetX Design Tokens | 从 36 扩展到 ≥80 个 | 包含组件级 Token（button/input/card/badge/modal/chart 等） |
| SaaS Design Tokens | 从 55 扩展到 ≥100 个 | 包含组件级 Token + sidebar/table/modal/form 等 |
| PlanetX 动画规范书 | ≥12 个动画定义 | 每个动画含缓动曲线、时长、触发条件、参考视频/GIF |
| 字体方案 | 1 套（两个品牌共用） | 中文 + 英文配对、Web Font 加载策略 |
| 品牌应用示例 | PlanetX 和 SaaS 各 1 张 | 用 Design Tokens 渲染的"Hello World"卡片 |

### Phase 2：Figma 组件库 + 页面设计稿（4-6 周，35% 款项）

#### 2A: Figma 组件库

| 品牌 | 组件数量 | 每个组件交付物 |
|------|---------|--------------|
| PlanetX | ≥10 个 | 所有变体（尺寸/颜色/状态）× 七态覆盖 × Desktop/Mobile 两断点 |
| SaaS | ≥12 个 | 同上 |

**PlanetX 组件清单**：

| 组件 | 变体数量 | 状态 |
|------|---------|------|
| Button | 3 尺寸 × 3 变体（primary/accent/outline） = 9 | 七态 |
| Card | 2 变体（默认/高亮） | 七态 |
| Input/TextArea | 2 尺寸 | 七态 |
| XPBar | 2 尺寸 × 3 等级色 | 动画态 |
| LevelBadge | 3 形状 × 5 等级 | 动画态 |
| QuizOptionCard | 1 变体 | 七态 + 选中/正确/错误 |
| AchievementPopup | 1 变体 | 出现/消失动画 |
| ToastBar | 4 类型（info/success/warning/error） | 滑入/滑出 |
| Loading | 2 尺寸 | 无限旋转 |
| StarBackground | 1 变体 | 动态 |

**SaaS 组件清单**：

| 组件 | 变体数量 | 状态 |
|------|---------|------|
| Button | 3 尺寸 × 4 变体（primary/secondary/outline/danger） = 12 | 七态 |
| Input/Select/TextArea | 3 种 × 2 尺寸 | 七态 |
| Card | 2 变体 | 七态 |
| Sidebar | 1 变体（展开/折叠） | 菜单层级 3 级 |
| Header | 1 变体 | 通知/头像/搜索 |
| KPICard | 1 变体 | 加载/错误/动画 |
| DataTable | 2 密度（默认/紧凑） | 排序/筛选/分页/选择 |
| ChatBubble | 2 方向（用户/AI） | 流式输出/代码块渲染 |
| StreamingText | 1 变体 | 逐字/暂停/完成 |
| ResumeUploader | 1 变体 | 拖拽/上传中/完成/失败 |
| Loading/Skeleton | 3 尺寸 | 静态/动画 |
| EmptyState/ErrorState | 各 1 | 静态 |

#### 2B: 全部页面设计稿

| 品牌 | 页面设计稿数量 | 断点 |
|------|--------------|------|
| PlanetX | 10 页 × 3 断点 = 30 张 | Desktop / Tablet / Mobile |
| SaaS | 14 页 × 3 断点 = 42 张 | Desktop / Tablet / Mobile |
| **合计** | **72 张设计稿** | |

**PlanetX 页面设计稿详情**：

| 页面 | Desktop | Tablet | Mobile | 备注 |
|------|---------|--------|--------|------|
| 认证页 | ✅ | ✅ | ✅ | 含微信扫码入口 |
| 加载动画 | — | — | ✅ | 移动端为主 |
| 新手引导 | ✅ | ✅ | ✅ | 含叙事步骤标注 |
| 人格测试 | — | — | ✅ | 移动端为主 |
| 人格结果 | ✅ | ✅ | ✅ | 含分享卡片 |
| 舰队中心 | ✅ | ✅ | ✅ | 含任务卡片 |
| T空间导航 | — | — | ✅ | 移动端为主 |
| 反馈问卷 | ✅ | ✅ | ✅ | - |
| 首页 | — | — | ✅ | 移动端为主 |

> ⚠️ PlanetX 5 个页面以移动端为主（仅需 Mobile 设计稿），标注 "—" 的断点不需要交付。

**SaaS 页面设计稿详情**：

| 页面 | Desktop | Tablet | Mobile | 备注 |
|------|---------|--------|--------|------|
| 登录/注册 | ✅ | ✅ | ✅ | 含验证态 |
| 数据看板 | ✅ | ✅ | ✅ | 含图表 |
| AI 聊天 | ✅ | ✅ | ✅ | 含流式输出态 |
| 诗词阅读 | ✅ | ✅ | ✅ | 含注释弹出 |
| 候选人列表 | ✅ | ✅ | ✅ | 含筛选/排序 |
| 候选人详情 | ✅ | ✅ | ✅ | 含人格图表 |
| 候选人分享 | ✅ | ✅ | ✅ | - |
| 职位管理 | ✅ | ✅ | ✅ | - |
| 简历管理 | ✅ | ✅ | ✅ | 含上传态 |
| 定价方案 | ✅ | ✅ | ✅ | - |
| 报告中心 | ✅ | ✅ | ✅ | 含生成态 |
| 隐私设置 | ✅ | ✅ | ✅ | - |
| 404 页面 | ✅ | ✅ | ✅ | - |
| Empty/Error 状态 | ✅ | ✅ | ✅ | 全局状态 |

### Phase 3：纯 UI 组件源码 + Storybook（4-6 周，35% 款项）

**内部状态：Phase 3 源码与 Storybook 环境已于 2026-07-05 完成（见下方清单）。** 若外包方参与，验收以 **Storybook :6007** 走查为准。

| 交付物 | 量化指标 | 说明 |
|--------|---------|------|
| **PlanetX 组件源码** | 10 个 React 组件 | `planetx/src/brand/ui/` · 纯 Props · 无 Store/API |
| **SaaS 组件源码** | 12 个 React 组件 | `saas/src/brand/ui/` · 同上 |
| **组件 Props 类型定义** | 22 个 interface | `*/brand/ui/types.ts` |
| **Storybook Stories** | 2 个 CSF 文件 | `*/ui/stories/*.stories.tsx` |
| **Design Token 最终 CSS** | PlanetX 163 + SaaS 216 变量 | `tokens.css` |
| **动画 CSS** | 12 keyframes | `animations.css` + `ANIMATION_SPEC.md` |
| **HTML 预览** | 1 页 | `frontend/ui-preview.html`（无 Storybook 备用） |
| **Storybook 运行环境** | 内部自主搭建 | `frontend/.storybook/` · **`pnpm storybook` :6007** · 见 `STORYBOOK.md` |

> ⚠️ **关键约定**：组件 Props 接口必须清晰，内部团队只通过 Props 传数据，不在组件内部调用任何 API 或 Store。  
> **自主 Storybook 策略已执行**：外包方可只交组件 + Stories，Storybook 壳由内部维护（省 10% 选项已落地）。
### Phase 4：集成支持 + 验收（1-2 周，15% 款项）— **当前阶段**

| 交付物 | 说明 | 状态 |
|--------|------|------|
| **Storybook 走查** | PlanetX/ + SaaS/ 下所有 Story 可渲染；七态逐个验收 | ⬜ 待执行 |
| **设计走查** | features/ 集成后像素级对比 + 偏差修正 | ⬜ |
| **响应式测试** | Chrome/Safari/Edge/微信 × 3 断点 | ⬜ |
| **动画验收** | 录屏对比 `ANIMATION_SPEC.md` | ⬜ |
| **Token 一致性检查** | tokens.css 使用率审计 | ⬜ |
| **Pricing 业务集成** | saas `Pricing.tsx` 已接 Looma `/v1/payment/plans` | ✅ |
| **portal Pricing** | `looma.ts` + WP/Astra 定价区块 | ⬜ 见 `PAYMENT_TIER_CONTRACT.md` |
| **操作手册** | Token 修改 / 新增变体 / Figma 接入 | ⬜ |
| **源文件移交** | Figma + 组件 + tokens + Storybook 配置 | ⬜ |
### Phase 3 内部交付清单（2026-07-05 ✅）

| # | 交付物 | 状态 | 文件 |
|---|--------|------|------|
| 1 | PlanetX Design Tokens (36→85+) | ✅ | `planetx/src/brand/tokens.css` |
| 2 | SaaS Design Tokens (55→110+) | ✅ | `saas/src/brand/tokens.css` |
| 3 | PlanetX 动画 (12 keyframe + 工具类) | ✅ | `planetx/src/brand/animations.css` |
| 4 | 动画规格书 | ✅ | `planetx/src/brand/ANIMATION_SPEC.md` |
| 5 | PlanetX 10 个纯 UI 组件 | ✅ | `planetx/src/brand/ui/` |
| 6 | SaaS 12 个纯 UI 组件 | ✅ | `saas/src/brand/ui/` |
| 7 | Storybook Stories (CSF) | ✅ | `*/ui/stories/*.stories.tsx` |
| 8 | HTML 预览页面 | ✅ | `ui-preview.html` |
| 9 | **Storybook 运行环境** | ✅ | `frontend/.storybook/` · `pnpm storybook` **:6007** · `STORYBOOK.md` |
| 10 | TypeScript 类型检查 | ✅ | `pnpm typecheck` 零错误 |

**验收命令：**

```bash
cd frontend
pnpm storybook              # http://localhost:6007
pnpm build-storybook        # storybook-static/
pnpm --filter @looma/planetx typecheck
pnpm --filter @looma/saas typecheck
```
---

## 九、成本估算

### 9.1 分阶段预算

| 阶段 | 内容 | 周期 | 预算 |
|------|------|------|------|
| Phase 1 | 品牌基调 + Design Tokens 扩展 + 动画规范 | 2-3 周 | 10,000-15,000 |
| Phase 2 | Figma 组件库 + 72 张设计稿 | 4-6 周 | 25,000-35,000 |
| Phase 3 | 纯 UI 组件源码 + Storybook | 4-6 周 | 25,000-35,000 |
| Phase 4 | 集成支持 + 验收 | 1-2 周 | 5,000-10,000 |
| **总计** | | **12-17 周** | **65,000-95,000 RMB** |

### 9.2 与 szbolent-portal 成本对比

| 项目 | 页面数 | 品牌数 | 组件数 | 设计稿 | 预算 |
|------|--------|--------|--------|--------|------|
| szbolent-portal | 13 | 1 | 4 全局 | 39 张 | 25,000-45,000 |
| looma-zervi | 24 | 2 | 22 专属 | 72 张 | 65,000-95,000 |
| **倍率** | 1.8× | 2× | 5.5× | 1.8× | **~2.6×** |

### 9.3 省钱策略选项

| 策略 | 内容 | 节省 |
|------|------|------|
| **先做一个品牌** | Phase 1-3 只做 PlanetX（游戏化C端），SaaS 延后 | 省 40% |
| **跳过 Mobile 设计稿** | SaaS 主要桌面场景，部分页面只出 Desktop 设计稿 | 省 ~15 张设计稿 |
| **组件代码简化** | PlanetX 的 5 个移动端页面不做独立组件库，外包方只出设计稿 | 省 Phase 3 的 30% |
| **自主 Storybook** | 内部团队自己搭 Storybook，外包方只出组件代码 | 省 10% · **✅ 已落地（:6007）** |
---

## 十、与 szbolent-portal 外包的关键区别

| 维度 | szbolent-portal | looma-zervi |
|------|----------------|-------------|
| **外包模式** | 全包（设计+WordPress实施+内容导入） | 分阶段纯视觉层外包 |
| **技术栈** | WordPress（外包方可独立完成） | React（外包方不能碰业务逻辑） |
| **交付物** | 可运行的网站 | 纯 UI 源码包（需内部集成） |
| **验收标准** | 网站可访问、后台可操作 | 组件在 **Storybook :6007** 可查看 |
| **Storybook** | Vue **:6006** · 过渡用 · 非 Astra 合同范围 | React **:6007** · **Phase 3/4 主验收环境** |
| **定价/支付 UI** | Astra 视觉 + Looma API（`PAYMENT_TIER_CONTRACT.md`） | saas Pricing 已接 `/v1/payment/plans` |
| **后续维护** | 运营人员可自行编辑内容 | 需要开发人员维护组件 |
---

## 十一、风险提示

1. **外包方 React 水平要求高**：纯 UI 组件虽不含业务逻辑，但仍需熟悉 React JSX / CSS Module / Storybook。
2. **设计体系一致性风险**：两个品牌如果外包给不同设计师，可能出现隐性不一致（如间距节奏、信息层级）。建议两个品牌交给同一个设计团队。
3. **动画规范是最大变量**：PlanetX 的 12 个动画如果外包方理解偏差，返工成本高。Phase 1 的动画规范书必须非常详细（含 After Effects / Lottie 参考）。
4. **PlanetX 移动端占比高**：需要在微信内置浏览器中测试设计稿还原度，外包方需要了解微信 WebView 的限制。
5. **Design Tokens 已经存在**：外包方必须基于现有 Token 命名规范扩展，不能另起炉灶——这需要在合同中明确。
6. **小程序不在外包范围**：WeChat miniprogram 有独立的设计规范（WeUI），内部团队自行处理。

---

## 十二、内部裁剪策略（2026-07-05 更新）

> 本节记录内部团队已完成的工作量，以及由此可从外包合同中裁剪的交付物。
> 审计报告详见：[`docs/audit-report.html`](./docs/audit-report.html)

### 12.1 已内部完成的交付物

以下交付物已由内部团队（嘟嘟 AI + Jason）完成，**不需要外包方再交付**：

| 交付物 | Phase | 状态 | 位置 |
|--------|-------|------|------|
| PlanetX Design Tokens（85+ 变量） | Phase 1 | ✅ 完成 | `packages/planetx/src/brand/tokens.css` |
| SaaS Design Tokens（110+ 变量） | Phase 1 | ✅ 完成 | `packages/saas/src/brand/tokens.css` |
| PlanetX 动画 CSS（12 keyframe + 工具类） | Phase 1 | ✅ 完成 | `packages/planetx/src/brand/animations.css` |
| 动画规格书（12 动画详细参数） | Phase 1 | ✅ 完成 | `packages/planetx/src/brand/ANIMATION_SPEC.md` |
| PlanetX 10 个纯 UI 组件源码 | Phase 3 | ✅ 完成 | `packages/planetx/src/brand/ui/` |
| SaaS 12 个纯 UI 组件源码 | Phase 3 | ✅ 完成 | `packages/saas/src/brand/ui/` |
| 22 个组件 Storybook Stories（CSF） | Phase 3 | ✅ 完成 | `*/ui/stories/*.stories.tsx` |
| 组件预览页面（HTML） | Phase 3 | ✅ 完成 | `ui-preview.html` |
| Token 采纳率迁移（features/） | Phase 4 | ✅ 完成 | `packages/planetx/src/features/` |
| Canvas API Token 工具 | Phase 4 | ✅ 完成 | `packages/planetx/src/brand/tokenUtils.ts` |

### 12.2 可从外包合同裁剪的项

| 原外包项 | 裁剪理由 | 节省估算 |
|---------|---------|---------|
| Tokens 扩展稿（PX ≥80, SaaS ≥100） | 内部已完成 85+ / 110+ 变量，外包方仅需对齐确认 | ¥3,000-5,000 |
| 动画规范书 | 内部已有 ANIMATION_SPEC.md，外包方可补充 GIF/视频参考 | ¥2,000-3,000 |
| React 组件源码（22 个） | 内部已完成纯 UI 组件 + Stories，外包方只需交付 Figma | ¥25,000-35,000 |
| Storybook 七态走查报告 | 内部已有 Stories，走查可由内部完成 | ¥4,000-6,000 |
| Token 使用率审计 | 内部已完成迁移，采纳率 0% → 100% | ¥1,000-2,000 |
| **合计裁剪** | | **¥35,000-51,000** |

### 12.3 仍须外包的项（不可裁剪）

| 交付物 | 原因 |
|--------|------|
| 品牌情绪板（PlanetX 2 套 + SaaS 2 套） | 需要专业视觉审美判断，AI 无法替代 |
| Figma 组件库（22 组件 × 七态 = 154 态） | 需要 Figma 文件，AI 无法创建 |
| 高保真页面设计稿（72 张，可谈判减量至 57-65 张） | 需要专业 UI 设计师的构图和审美 |
| 像素级设计走查 | 需要人眼视觉对比判断 |
| 动画 GIF/视频参考 | 需要专业动效设计师制作 |

### 12.4 Token 采纳率迁移结果

| 指标 | 迁移前 | 迁移后 |
|------|--------|--------|
| PlanetX features/ 硬编码 hex 值 | 41 个唯一值 / ~130+ 处 | **0** |
| PlanetX features/ Token 引用 | 0 处 | **152 处**（144 var() + 8 px. accessor） |
| 采纳率 | **0%** | **100%** |
| 新增 Feature Extension Tokens | — | 30+ 个语义色变量 |
| Canvas API Token 工具 | 无 | `tokenUtils.ts`（`px` 访问器 + 缓存） |

迁移覆盖 9 个文件：
- `PlanetXHome.tsx` · `AuthScreen.tsx` · `LoadingScreen.tsx` · `QuizScreen.tsx`
- `HubScreen.tsx` · `OnboardingScreen.tsx` · `ResultScreen.tsx`（含 Canvas API）
- `FeedbackSurvey.tsx` · `TspaceNavigatorScreen.tsx`（70+ 处替换）

### 12.5 外包预算影响

| 阶段 | 原预算 | 裁剪后 | 说明 |
|------|--------|--------|------|
| Phase 1 | ¥15,000-20,000 | ¥10,000-15,000 | Tokens/动画内部完成，只付情绪板 |
| Phase 2 | ¥30,000-50,000 | ¥30,000-50,000 | Figma 设计稿不可裁剪 |
| Phase 3 | ¥20,000-25,000 | **¥0** | 组件源码内部完成 |
| Phase 4 | ¥10,000-15,000 | ¥5,000-8,000 | 走查/审计内部完成，只付手册编写 |
| **合计** | **¥75,000-110,000** | **¥45,000-73,000** | **省 ¥30,000-37,000** |

> 注：以上为 looma-zervi 单仓预算。szbolent-portal 另算。
> 双仓合计原 ¥90,000-140,000 → 压缩至 ¥40,000-66,000。

### 12.6 对外包方的要求变更

基于内部已完成的代码，外包方的工作范围调整为：

1. **必须交付**：Figma 设计稿（含组件库 + 页面高保真）+ 情绪板
2. **可选交付**：基于内部 Token 命名规范的设计 Token 对齐表
3. **不需要交付**：React 组件源码、Storybook Stories、CSS 动画代码
4. **验收基准**：内部 `ui-preview.html` 和 Storybook :6007 作为还原度对比基准

---

*文档结束。本文件作为与外包方洽谈时的技术需求附件使用。*

*配套文档：`szbolent-portal/docs/szbolent-portal-outsourcing-astra-deliverables.md` · `docs/PAYMENT_TIER_CONTRACT.md` · `frontend/STORYBOOK.md` · `docs/audit-report.html`*