# 前端多端一致性整改报告

> **版本**: v1.0  
> **日期**: 2026-07-03  
> **范围**: `planetx`（C端Web） · `saas`（B端Web） · `miniprogram`（微信小程序） · `shared-core`（共享契约）  
> **审核**: 待前端项目组全员 Review

---

## 1. 背景与目的

looma-zervi 前端包含三个独立交付端 + 一个共享契约包。在多端并行开发的过程中，积累了一定的技术债与一致性缺口。本报告梳理了发现的 9 个核心问题，给出了具体整改方案、工作量预估与验收标准，供项目组排期执行。

---

## 2. 发现摘要

| # | 问题 | 严重度 | 影响范围 | 预计工时 |
|---|------|--------|----------|----------|
| 1 | 小程序未引用 `@looma/shared-core` | 🔴 致命 | miniprogram 全部类型/常量/API | 5d |
| 2 | 题库 & 人格数据在 planetx 和 miniprogram 中重复 | 🔴 高 | 题库新增 → 两端手动同步 | 2d |
| 3 | 合规模块（PIPL）在 miniprogram 中独立硬编码 | 🔴 高 | 合规范围变更可能遗漏 | 1d |
| 4 | API Client 在多端各自实现 | 🟡 中 | 401处理、超时、日志格式不统一 | 3d（含小程序适配） |
| 5 | Design Token 无跨品牌规范 | 🟡 中 | 微交互手感不一致 | 1.5d |
| 6 | 同名组件事实上无复用 | 🟡 中 | ConsentModal / ErrorBoundary / XPBar 各有三套 | 2d（逻辑抽取） |
| 7 | Auth Guard 行为差异 | 🟡 中 | PlanetX无loading; SaaS有loading; 小程序无guard | 1d |
| 8 | 状态管理机制不统一 | 🟢 低 | 未来跨端状态共享困难 | 按需 |
| 9 | 小程序 ↔ SaaS 数据桥接缺失 | 🟢 低 | B端HR无法在小程序查看候选数据 | 按需 |

---

## 3. 详细问题与整改方案

---

### 问题 1：小程序未引用 `@looma/shared-core`（🔴 致命）

**现状**

```
miniprogram/
├── types/index.ts         ← 157行手工镜像 shared-core/src/types/
├── constants/quiz.ts      ← 157行与 planetxAuthStore 完全重复
├── utils/api.ts           ← 287行自实现 MiniApiClient
├── utils/consent.ts       ← 79行手工镜像 shared-core/src/compliance/
├── utils/analytics.ts     ← 47行基础实现，未复用 shared-core/src/analytics/
└── （无 package.json）
```

小程序没有通过 npm 依赖 `@looma/shared-core`，所有类型、常量、工具函数都是手工复制。

**根因**: 小程序项目初始化较早，shared-core 是后续提取的。可能是微信小程序对 npm 包支持（需要构建工具处理）导致了依赖障碍。

**整改方案**

1. **创建 `miniprogram/package.json`**
   - 接入 monorepo workspace（`"@looma/shared-core": "workspace:*"`）
   - 配置微信小程序 npm 构建（开发者工具 → 工具 → 构建 npm）

2. **删除重复代码并改为 import**

   | 文件 | 操作 |
   |------|------|
   | `miniprogram/types/index.ts` | 删除 `User`, `UserProfile`, `AuthResponse`, `Tier`, `Role`, `QuotaRecord`, `QuotaResponse`, `Identity`, `IDENTITY_LABELS`, `TraitKey`, `PersonalityType`, `QuizOption`, `QuizQuestion`, `MissionId`, `Fleet`, `RankName`, `getRankName`, `GameProfile`, `DocSource`, `ChatMessage`, `AskResponse`, `RESOURCE_ASK/JOB_MATCH/RESUME_PARSE`, `QUOTA_LIMITS`, `BRAND` → 全部改为 `import { ... } from '@looma/shared-core'` |
   | `miniprogram/types/index.ts` | **保留** `AppEvent` 类型（仅小程序端使用的事件总线类型） |

3. **处理 shared-core 中当前缺失的导出**
   
   需在 `shared-core/src/index.ts` 中补充导出：
   - `IDENTITY_LABELS`（当前仅在 planetxAuthStore 中内联定义）
   - `getRankName`（当前在 `@@/types/game` 中通过 `RANK_NAMES` 导出，但 `getRankName` 函数未导出）
   - `QUIZ_QUESTIONS` / `PERSONALITY_MAP` / `computePersonality`（见问题 2）

4. **接入 shared-core analytics**
   - 将 `miniprogram/utils/analytics.ts` 的 `trackMiniEvent` 改为调用 `shared-core` 的 `trackEvent`

**验收标准**
- [ ] `miniprogram` 目录下有 `package.json` 且包含 `@looma/shared-core` 依赖
- [ ] 微信开发者工具 "构建 npm" 后无报错
- [ ] `miniprogram/types/index.ts` 仅保留 `AppEvent` 类型
- [ ] `miniprogram/utils/consent.ts` 中的 `ConsentScope`、`LABELS`、`DESCRIPTIONS`、`ensureConsent` 逻辑改为从 shared-core 导入
- [ ] 全量回归：splash → auth → quiz → result → hub 主流程无异常

**预估工时**: **5 人天**（含适配调试）

---

### 问题 2：题库 & 人格数据重复维护（🔴 高）

**现状**

`QUIZ_QUESTIONS`（8道题 × 4选项 × 多行 = 约180行）和 `PERSONALITY_MAP`（6种人格 × 多行 = 约60行）在两个文件中**逐字完全一致**：

- `planetx/src/features/auth/planetxAuthStore.ts` (L107-L231)
- `miniprogram/constants/quiz.ts` (L9-L157)

`computePersonality()`、`hydratePersonality()`、`getShareText()` 等函数也完全重复。

**风险**: 产品/运营新增第9道题或调整人格描述时，开发必须同时修改两个文件。已发生过"planetx 更新了题库但小程序未同步"吗？（建议做一次 diff 验证）

**整改方案**

在 `shared-core` 中新增 `src/constants/quiz.ts` 和 `src/constants/personality.ts`：

```
shared-core/src/constants/
├── quiz.ts              ← QUIZ_QUESTIONS 题库
├── personality.ts       ← PERSONALITY_MAP + FALLBACK_MAP
```

新增工具函数导出：

```
shared-core/src/utils/
├── quiz.ts              ← computePersonality, hydratePersonality
├── share.ts             ← getShareText (通用版, platform 参数由各端传入)
```

`planetxAuthStore.ts` 和 `miniprogram/constants/quiz.ts` 改为：

```typescript
import { QUIZ_QUESTIONS, computePersonality, hydratePersonality, getShareText } from '@looma/shared-core'
// 删除原本地定义
```

**注意**: `getShareText` 在 planetx Web 端有 4 种平台文案（wechat/xiaohongshu/weibo/copy），小程序端只有 1 种。建议将模板提取到 shared-core，各端按需调用。

**验收标准**
- [ ] `shared-core/src/constants/quiz.ts` 通过所有端测试
- [ ] `planetxAuthStore.ts` 中 `QUIZ_QUESTIONS` / `PERSONALITY_MAP` 等定义改为 import
- [ ] `miniprogram/constants/quiz.ts` 文件中定义改为 import，文件保留仅做 re-export 兼容
- [ ] planetx 和 miniprogram 跑通完整 8 题测评流程

**预估工时**: **2 人天**

---

### 问题 3：合规模块（PIPL）碎片化（🔴 高）

**现状**

`ConsentScope` 枚举、`LABELS`、`DESCRIPTIONS`、`ensureConsent` 逻辑存在于三处：

| 位置 | 方式 |
|------|------|
| `shared-core/src/types/compliance.ts` | 权威定义 ✅ |
| `planetx/src/compliance/useConsent.tsx` + `ConsentModal` | 正确引用 shared-core ✅ |
| `saas/src/compliance/useConsent.tsx` + `ConsentModal` | 正确引用 shared-core ✅ |
| `miniprogram/utils/consent.ts` | **自实现**：硬编码类型、标签、描述 🔴 |

小程序使用 `wx.showModal` 展示同意弹窗，而不是自定义 UI 组件（这是平台限制，可以接受）。但类型和文案应该从 shared-core 获取。

**合规风险**: 若监管部门要求新增 consent scope（如 `voice_collection`），后端和 shared-core 会更新，但小程序端如果忘记同步 `miniprogram/utils/consent.ts`，会出现"功能使用了但未合规弹窗"的严重法律风险。

**整改方案**

`miniprogram/utils/consent.ts` 重构为：

```typescript
import { 
  ensureConsent as ensureConsentApi, 
  type ConsentScope, 
  CONSENT_SCOPE_LABELS, 
  CONSENT_SCOPE_DESCRIPTIONS 
} from '@looma/shared-core'
import { complianceApi } from './api'

// 缓存机制保留
const cache: Partial<Record<ConsentScope, boolean>> = {}

export async function ensureConsent(scope: ConsentScope): Promise<boolean> {
  if (cache[scope]) return true
  return new Promise((resolve) => {
    wx.showModal({
      title: `需要授权：${CONSENT_SCOPE_LABELS[scope]}`,
      content: CONSENT_SCOPE_DESCRIPTIONS[scope],
      confirmText: '同意',
      cancelText: '取消',
      success: async (res) => {
        if (!res.confirm) { resolve(false); return }
        try {
          await complianceApi.grant(scope)
          cache[scope] = true
          resolve(true)
        } catch { resolve(false) }
      },
      fail: () => resolve(false),
    })
  })
}
```

**验收标准**
- [ ] 小程序 `utils/consent.ts` 中不再硬编码 `ConsentScope` / `LABELS` / `DESCRIPTIONS`
- [ ] `ensureConsent` 行为不变（先检查缓存 → 后端状态 → wx.showModal → grant）
- [ ] 检查所有调用 `ensureConsent` 的位置仍正常工作

**预估工时**: **1 人天**

---

### 问题 4：API Client 各端自行实现（🟡 中）

**现状对比**

| 特性 | shared-core `ApiClient` | miniprogram `MiniApiClient` | 差异 |
|------|--------------------------|---------------------------|------|
| 传输层 | `fetch()` | `wx.request()` | 平台限制，可接受 |
| 401 处理 | 清除 token + 调用 `onUnauthorized` | 清除 token + 触发 `eventBus('auth:expired')` + `store.reset()` | 机制不同但效果等价 |
| 超时 | AbortController + 默认 30s | `wx.request({ timeout })` + 默认 10s | 🔴 **默认值不一致** |
| Token 获取 | `getToken()` 回调/StorageAdapter | `getToken()` 回调 | 等价 |
| 错误响应解析 | 尝试 JSON，回退到文本 | 只读 `resp.data.message` | 🟡 微信端更容错 |
| Stream/Upload | ✅ SSE + FormData | ❌ 不支持 | 规划中 |
| Query String | ✅ `buildQueryString` | ❌ 不处理 params | 小程序暂不需要 |

**整改方案**

`MiniApiClient` 不应被完全替换（`wx.request` 与 `fetch` 底层不同），但应**对齐行为**：

1. 实现 `ApiClient` 同款接口：
   ```typescript
   import { ApiClient } from '@looma/shared-core'
   // MiniApiClient 应实现与 ApiClient 相同的公共方法签名
   ```

2. 统一超时默认值：MiniApiClient 从 10s 改为 30s（与 web 端对齐）

3. 统一错误解析逻辑：实现与 `ApiClient.parseError` 相同的行为

4. 将 `StorageAdapter` 模式改为 `getToken` 回调：
   ```typescript
   // 当前：从 store 直接获取
   getToken: () => store.get('token')
   // 改为：通过 getToken 回调，与 web 端一致
   ```

**验收标准**
- [ ] `MiniApiClient` 超时默认值 = 30000ms
- [ ] 错误响应解析逻辑与 `ApiClient.parseError` 一致
- [ ] 401 行为：清除 token → `store.reset()` → `eventBus.emit('auth:expired')` → `onUnauthorized()`
- [ ] 所有 API 调用不受影响

**预估工时**: **3 人天**（含适配调试）

---

### 问题 5：Design Token 无跨品牌规范（🟡 中）

**现状**

三端的 CSS 变量命名空间各不同：

| 端 | 前缀 | 数量 |
|---|------|------|
| planetx | `--px-color-*`, `--px-spacing-*`, `--px-radius-*`, `--px-shadow-*` | ~25 个 |
| saas | `--color-*`, `--radius-*`, `--shadow-*`（无前缀） | ~25 个 |
| miniprogram | 无变量，硬编码颜色值 | N/A |

两个品牌视觉差异巨大（这是有意的），但**无公共规范**导致：
- 按钮大小、按压力度、动画时长等"手感"不一致
- 新加入的开发者不知道该用哪个变量

**整改方案**

在 `shared-core` 中创建一份**品牌无关的基础规范**：

```
shared-core/src/tokens/
├── base.css             ← 公共间距/字号/动画（不包含颜色）
└── README.md            ← Token 使用规范文档
```

`base.css` 示例：
```css
:root {
  /* 公共间距（跨品牌一致） */
  --looma-space-xs: 4px;
  --looma-space-sm: 8px;
  --looma-space-md: 16px;
  --looma-space-lg: 24px;
  --looma-space-xl: 32px;
  --looma-space-2xl: 48px;

  /* 公共圆角 */
  --looma-radius-sm: 6px;
  --looma-radius-md: 8px;
  --looma-radius-lg: 12px;
  --looma-radius-xl: 16px;
  --looma-radius-full: 9999px;

  /* 公共动画 */
  --looma-transition-fast: 150ms ease;
  --looma-transition-normal: 250ms ease;
  --looma-transition-slow: 400ms ease;

  /* 公共阴影层级 */
  --looma-shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
  --looma-shadow-md: 0 4px 6px rgba(0,0,0,0.08);
  --looma-shadow-lg: 0 10px 20px rgba(0,0,0,0.12);

  /* 公共字体大小 */
  --looma-font-xs: 10px;
  --looma-font-sm: 12px;
  --looma-font-md: 14px;
  --looma-font-lg: 16px;
  --looma-font-xl: 18px;
  --looma-font-2xl: 24px;
}
```

各端 tokens.css 改为叠加模式：
```css
/* planetx/src/brand/tokens.css */
@import '@looma/shared-core/tokens/base.css';

:root {
  --px-color-primary: #6C63FF;
  /* ... planetx 特定颜色变量 */
}
```

**验收标准**
- [ ] `shared-core/src/tokens/base.css` 定义约 20 个基础 token
- [ ] planetx 和 saas 的 tokens.css 改为 `@import` base.css
- [ ] 两个端视觉效果无变化（回归截图对比）

**预估工时**: **1.5 人天**

---

### 问题 6：同名组件零复用（🟡 中）

**现状**

| 组件 | planetx | saas | miniprogram |
|------|---------|------|-------------|
| ConsentModal | ✅ 134行（星空紫色毛玻璃） | ✅ 87行（白色卡片） | ❌ wx.showModal |
| ErrorBoundary | ✅ 200行（星空+粒子动画） | ✅ 165行（简洁白底） | ❌ 无 |
| XPBar | ✅ 74行（带等级徽章） | ❌ 无 | ✅ 14行（WXS计算版） |
| AchievementPopup | ✅ 存在于brand/components | ❌ 无 | ✅ 独立component |
| StarBackground | ✅ 品牌组件 | ❌ 无 | ✅ 独立component |

- **逻辑层完全一致**，仅 UI 渲染不同
- 例如 ConsentModal: 流程都是 `显示scope描述 → 用户点击 → resolve(true/false)`，差异仅在于 CSS

**整改方案**

**方案 A（推荐）: 提取核心逻辑到 shared-core**

```
shared-core/src/components/
├── ConsentLogic.ts        ← 状态管理、API调用、回调处理
├── ErrorBoundaryCore.tsx  ← 错误捕获、堆栈格式化
└── XPBarLogic.ts          ← 进度百分比计算、等级称号映射
```

各端只写 UI 壳：
```tsx
// planetx/src/brand/components/ConsentModal.tsx
import { useConsentLogic } from '@looma/shared-core/components/ConsentLogic'

export default function ConsentModal({ scope, onAccept, onDecline }) {
  const { title, description, handleAccept, handleDecline } = useConsentLogic({ scope, onAccept, onDecline })
  return <div className="px-consent-modal">{/* PlanetX 星空 UI */}</div>
}
```

**方案 B: 将 planetx/saas 的同名组件统一到一个品牌组件库中**

不推荐，因为两个品牌的视觉差异是有意为之。

**本次建议实施范围**

先抽取 `ErrorBoundary` 和 `ConsentModal` 的逻辑层（因为代码量最大且复用价值最高）。`XPBar` 放在下个迭代。

**验收标准**
- [ ] `ErrorBoundary` 的错误捕获/重置/开发模式调试逻辑通过 shared-core 复用
- [ ] `ConsentModal` 的 scope 解析/API调用逻辑通过 shared-core 复用
- [ ] 三个端的组件行为无回归

**预估工时**: **2 人天**

---

### 问题 7：Auth Guard 行为差异（🟡 中）

**现状**

| 特性 | PlanetXAuthGuard | SaasAuthGuard | 小程序 |
|------|-----------------|---------------|--------|
| Token 校验 | ✅ 触发 loadProfile | ✅ 触发 fetchProfile | ❌ 无 guard 组件 |
| Loading 状态 | ❌ 无（闪屏闪烁） | ✅ "验证登录状态..." | N/A |
| 重定向 | → `/auth` | → `/login` | — |
| 自动登录 | ❌ | ✅ tryAutoLogin（C→B互通） | ✅ wx.login |

**问题**
- PlanetX AuthGuard 在校验期间无 loading 提示 → 用户看到的内容闪烁
- 小程序没有统一的路由守卫 → 每个页面 onShow 自行判断登录态

**整改方案**

统一 Auth Guard 行为规范（文档层面）：

1. Auth Guard 在校验期间**必须**显示 loading 状态
2. 401 时**必须**先清除 token 再跳转登录页
3. 小程序侧：提取登录态检查到 app.js 全局中间件（类似 page onShow 拦截器）

具体修改 `PlanetXAuthGuard` 增加 loading 状态（参照 SaasAuthGuard 实现）。

**验收标准**
- [ ] PlanetXAuthGuard 增加 loading 状态展示
- [ ] 小程序 hub/ask/profile 页面统一登录态检查逻辑

**预估工时**: **1 人天**

---

### 问题 8：状态管理机制不统一（🟢 低）

**现状**

| 端 | 状态管理 | 持久化 |
|---|---------|--------|
| planetx | Zustand `usePlanetXStore` | localStorage (token) + API (profile) |
| saas | Zustand `useSaasAuthStore` + `persist` 中间件 | localStorage (token via persist) |
| miniprogram | 自定义 `store` 对象 + `eventBus` | wx.storage (token) + API (profile) |

三个端使用了完全不同的状态管理范式。这导致共享状态逻辑无法抽取。

**整改方案**

属于长期重构项，不建议本阶段处理。影响评估：
- Web 两端使用 Zustand 是合理的，且 `useSaasAuthStore` 的 `persist` 中间件更先进
- 小程序端使用自定义 store + eventBus 是微信平台的惯用模式
- 短期内不影响一致性，但未来如果要实现"跨端状态共享"会很困难

**建议**: 在问题1（小程序接入shared-core）完成后，探索能否将 `planetxAuthStore` 和 `miniprogram/store.ts` 的核心状态定义提取到 shared-core，各端挂不同的持久化适配器。

**预估工时**: **按需**（本文档不排期）

---

### 问题 9：小程序 ↔ SaaS 数据桥接缺失（🟢 低）

**现状**

C→B 数据流：
- PlanetX Web → SaaS：✅ 正常（localStorage 共享 token + profileShareCode）
- 小程序 → SaaS：❌ 完全断开

意味着：小程序用户完成人格测试后，无法将结果分享给 T空间 B端 HR。HR 也无法在小程序内查看候选人。

**整改方案**

1. **小程序生成 profileShareCode**: 在小程序 profile 页面增加"生成分享链接"按钮，调用 `referralApi.create({ purpose: 'profile_share' })` 获取 code
2. **跨环境 URL scheme**: 小程序分享链接指向 Web 桥接页：
   ```
   https://t-space.example.com/bridge/mp?code=XXX
   ↓
   判断在微信内 → 引导打开小程序
   判断在浏览器 → 展示候选人详情页
   ```

**预估工时**: **按需**（产品决策后评估）

---

## 4. 实施路线图

### 第 1 阶段（Sprint 当前 +1）：架构债清理

| 顺序 | 任务 | 工时 | 负责人 |
|------|------|------|--------|
| 1.1 | 问题 2：题库/人格数据提取到 shared-core | 2d | |
| 1.2 | 问题 1：小程序接入 shared-core（依赖 1.1） | 5d | |
| 1.3 | 问题 3：合规代码改用 shared-core（依赖 1.2） | 1d | |
| **小计** | | **8d** | |

### 第 2 阶段（Sprint +2）：组件治理

| 顺序 | 任务 | 工时 | 负责人 |
|------|------|------|--------|
| 2.1 | 问题 5：Design Token 共享规范 | 1.5d | |
| 2.2 | 问题 6：ErrorBoundary + ConsentModal 逻辑抽取 | 2d | |
| 2.3 | 问题 7：Auth Guard 行为统一 | 1d | |
| 2.4 | 问题 4：API Client 行为对齐 | 3d | |
| **小计** | | **7.5d** | |

### 第 3 阶段（按需启动）

| 顺序 | 任务 | 工时 |
|------|------|------|
| 3.1 | 问题 8：状态管理统一（探索阶段） | TBD |
| 3.2 | 问题 9：小程序 ↔ SaaS 桥接 | TBD |

---

## 5. 风险与注意事项

1. **小程序 npm 构建兼容性**: 微信小程序对 npm 包的支持需要构建工具处理（需确认 `@looma/shared-core` 的 TypeScript 导出的兼容性）。可能需要为 shared-core 生成 `.js` 产物。

2. **回归范围大**: 问题 1（小程序接入 shared-core）几乎改动小程序每个文件。建议分步 PR，每改一个模块跑一次完整流程。

3. **平台限制**: 小程序不支持 `fetch()` 和 `FormData`，所以 API Client 和 upload/stream 功能需要保留平台适配层。

4. **团队协作**: `shared-core` 的变更需要**双人 Review**（Jason + szbenyx）。本次改动量大，建议安排专门时间做 Review。

5. **不要动视觉设计**: 本报告**不涉及**让 planetx 和 saas "看起来一样"——两个品牌的视觉差异化是有意为之的设计决策。整改仅聚焦于逻辑/行为/数据的一致性。

---

## 6. 附录：文件对照表

| 功能域 | shared-core | planetx | saas | miniprogram |
|--------|------------|---------|------|-------------|
| **类型定义** | `src/types/*.ts` | 通过 import | 通过 import | `types/index.ts` 🔴 重复 |
| **题库** | ❌ 缺失 | `planetxAuthStore.ts:107-180` | N/A | `constants/quiz.ts:9-82` 🔴 重复 |
| **人格匹配** | ❌ 缺失 | `planetxAuthStore.ts:183-231` | N/A | `constants/quiz.ts:85-157` 🔴 重复 |
| **API Client** | `api/ApiClient.ts` | 通过 `createApiClient` | 通过 `createSaasApiClient` | `utils/api.ts` 🔴 自实现 |
| **合规** | `compliance/ensureConsent.ts` | `compliance/useConsent.tsx` ✅ | `compliance/useConsent.tsx` ✅ | `utils/consent.ts` 🔴 自实现 |
| **Analytics** | `analytics/track.ts` | `analytics/usePlanetXAnalytics.ts` ✅ | `analytics/useSaasAnalytics.ts` ✅ | `utils/analytics.ts` 🔴 自实现 |
| **Auth Guard** | ❌ | `auth/PlanetXAuthGuard.tsx` | `auth/SaasAuthGuard.tsx` | 无（各页自行判断） |
| **ErrorBoundary** | ❌ | `brand/components/ErrorBoundary.tsx` | `brand/components/ErrorBoundary.tsx` | 无 |
| **ConsentModal** | ❌ | `brand/components/ConsentModal.tsx` | `brand/components/ConsentModal.tsx` | ❌ `wx.showModal` |
| **XPBar** | ❌ | `brand/components/XPBar.tsx` | N/A | `components/xp-bar/` |
| **Design Tokens** | ❌ | `brand/tokens.css` | `brand/tokens.css` | 硬编码 |

---

> **文档维护**: 每完成一个整改项后，请在此表格对应行打勾并备注日期。  
> **下次 Review**: Sprint +3 结束后，重新评估一致性评分。