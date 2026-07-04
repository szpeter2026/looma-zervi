# PlanetX 动画规格书

> 版本：1.0 | 更新日期：2026-07-05
> 适用范围：PlanetX 品牌（C端 游戏化）
> 文件位置：`packages/planetx/src/brand/animations.css`

---

## 动画总览

| # | 动画名 | 类名 | 用途 | 时长 | 缓动 |
|---|--------|------|------|------|------|
| 1 | starPulse | `.px-anim-starPulse` | 星空粒子闪烁 | 3s | ease-in-out, infinite |
| 2 | xSpin | `.px-anim-xSpin` | 品牌加载旋转 | 1.2s | linear, infinite |
| 3 | screenIn | `.px-anim-screenIn` | 页面入场 | 0.4s | ease-out |
| 4 | fadeIn | `.px-anim-fadeIn` | 渐进显示 | 0.3s | ease-out |
| 5 | claimPulse | `.px-anim-claimPulse` | 成就领取脉冲 | 0.6s | ease-out |
| 6 | levelUp | `.px-anim-levelUp` | 升级弹跳 | 0.8s | cubic-bezier(0.34, 1.56, 0.64, 1) |
| 7 | numberRoll | `.px-anim-numberRoll` | 数字滚动 | 0.5s | ease-out |
| 8 | glowPulse | `.px-anim-glowPulse` | 边框发光呼吸 | 2s | ease-in-out, infinite |
| 9 | slideInRight | `.px-anim-slideInRight` | 从右滑入 | 0.35s | ease-out |
| 10 | bounceIn | `.px-anim-bounceIn` | 弹跳进入 | 0.5s | cubic-bezier(0.34, 1.56, 0.64, 1) |
| 11 | shimmer | `.px-anim-shimmer` | 闪光扫过 | 2s | linear, infinite |
| 12 | particleFloat | `.px-anim-particleFloat` | 粒子上浮 | 8s | ease-in-out, infinite |

---

## 详细规格

### 1. starPulse — 星空粒子闪烁

| 属性 | 值 |
|------|-----|
| 时长 | 3s |
| 缓动 | ease-in-out |
| 迭代 | infinite |
| 触发条件 | StarBackground 组件挂载时自动播放 |
| 适用组件 | StarBackground |

**关键帧**:
```
0%, 100% → opacity: 0.15, scale(1)
50%       → opacity: 0.8, scale(2.2)
```

**说明**: 每颗星星的 animation-delay 随机化（0-4s），营造不同步的闪烁效果。

---

### 2. xSpin — 品牌加载旋转

| 属性 | 值 |
|------|-----|
| 时长 | 1.2s |
| 缓动 | linear |
| 迭代 | infinite |
| 触发条件 | LoadingScreen 显示时 / 数据请求中 |
| 适用组件 | Loading |

**关键帧**:
```
from → rotate(0deg)
to   → rotate(360deg)
```

**说明**: 匀速旋转，配合 logo 使用。可叠加 glowPulse 形成发光+旋转的双重效果。

---

### 3. screenIn — 页面入场

| 属性 | 值 |
|------|-----|
| 时长 | 0.4s |
| 缓动 | ease-out |
| 迭代 | once |
| 触发条件 | 路由切换 / 页面首次渲染 |
| 适用组件 | 所有 Screen 容器 |

**关键帧**:
```
from → opacity: 0, translateY(16px)
to   → opacity: 1, translateY(0)
```

**说明**: 轻微上移+淡入。配合 `--px-anim-normal` (250ms) 使用可加快节奏。

---

### 4. fadeIn — 渐进显示

| 属性 | 值 |
|------|-----|
| 时长 | 0.3s |
| 缓动 | ease-out |
| 迭代 | once |
| 触发条件 | 元素条件渲染（Toast、卡片切换） |
| 适用组件 | ToastBar, 卡片, 弹层 |

**关键帧**:
```
from → opacity: 0, translateY(8px)
to   → opacity: 1, translateY(0)
```

**说明**: 比 screenIn 更轻量，用于子元素级别的渐进出现。

---

### 5. claimPulse — 成就领取脉冲

| 属性 | 值 |
|------|-----|
| 时长 | 0.6s |
| 缓动 | ease-out |
| 迭代 | once |
| 触发条件 | 用户点击「领取」按钮 / 成就解锁瞬间 |
| 适用组件 | AchievementPopup |

**关键帧**:
```
0%   → scale(1), box-shadow: 0 0 0 0 rgba(255,215,0,0.5)
50%  → scale(1.05), box-shadow: 0 0 0 10px rgba(255,215,0,0)
100% → scale(1), box-shadow: 0 0 0 0 rgba(255,215,0,0)
```

**说明**: 金色脉冲扩散+轻微缩放。可叠加 `--px-shadow-gold` 增强效果。

---

### 6. levelUp — 升级弹跳

| 属性 | 值 |
|------|-----|
| 时长 | 0.8s |
| 缓动 | cubic-bezier(0.34, 1.56, 0.64, 1) — overshoot spring |
| 迭代 | once |
| 触发条件 | 用户等级提升 (level 变化) |
| 适用组件 | LevelBadge, XPBar |

**关键帧**:
```
0%   → scale(0.5) translateY(20px), opacity: 0
40%  → scale(1.2) translateY(-10px), opacity: 1
60%  → scale(0.95) translateY(0)
80%  → scale(1.05)
100% → scale(1) translateY(0), opacity: 1
```

**说明**: 弹簧曲线，先放大超出再回弹。配合 `numberRoll` 使用可形成数字+徽章同步升级的效果。

---

### 7. numberRoll — 数字滚动

| 属性 | 值 |
|------|-----|
| 时长 | 0.5s |
| 缓动 | ease-out |
| 迭代 | once |
| 触发条件 | XP 数值变化 / 等级数值变化 / 分数更新 |
| 适用组件 | XPBar (数字部分), ResultScreen (分数) |

**关键帧**:
```
0%   → translateY(100%), opacity: 0
50%  → opacity: 0.5
100% → translateY(0), opacity: 1
```

**说明**: 数字从下方滚入。内部团队可配合 JS 的 requestAnimationFrame 做数值递增动画。

---

### 8. glowPulse — 边框发光呼吸

| 属性 | 值 |
|------|-----|
| 时长 | 2s |
| 缓动 | ease-in-out |
| 迭代 | infinite |
| 触发条件 | 元素处于「高亮」状态 / hover 持续 |
| 适用组件 | QuizOptionCard (选中态), LevelBadge (高级别) |

**关键帧**:
```
0%, 100% → box-shadow: 0 0 8px rgba(200,255,80,0.15), border-color: rgba(200,255,80,0.2)
50%      → box-shadow: 0 0 24px rgba(200,255,80,0.4), border-color: rgba(200,255,80,0.5)
```

**说明**: 荧光绿呼吸光效，暗示「此元素可交互」或「此元素很重要」。

---

### 9. slideInRight — 从右滑入

| 属性 | 值 |
|------|-----|
| 时长 | 0.35s |
| 缓动 | ease-out |
| 迭代 | once |
| 触发条件 | 侧边面板打开 / 通知滑入 / 卡片切换 |
| 适用组件 | ToastBar (右出变体), HubScreen 面板 |

**关键帧**:
```
from → translateX(100%), opacity: 0
to   → translateX(0), opacity: 1
```

**说明**: 纯水平位移。配合 `translateX(-100%)` 可做反向滑出。

---

### 10. bounceIn — 弹跳进入

| 属性 | 值 |
|------|-----|
| 时长 | 0.5s |
| 缓动 | cubic-bezier(0.34, 1.56, 0.64, 1) — overshoot spring |
| 迭代 | once |
| 触发条件 | 弹窗出现 / 卡片首次渲染 / 结果揭示 |
| 适用组件 | AchievementPopup, ResultScreen |

**关键帧**:
```
0%   → scale(0.3), opacity: 0
50%  → scale(1.1), opacity: 0.8
70%  → scale(0.9)
100% → scale(1), opacity: 1
```

**说明**: 经典弹跳。比 levelUp 更通用，适合非升级场景的「惊喜出现」。

---

### 11. shimmer — 闪光扫过

| 属性 | 值 |
|------|-----|
| 时长 | 2s |
| 缓动 | linear |
| 迭代 | infinite |
| 触发条件 | 加载中骨架屏 / 高级卡片装饰 |
| 适用组件 | Loading (skeleton), LevelBadge (高级别装饰) |

**关键帧**:
```
0%   → background-position: -200% 0
100% → background-position: 200% 0
```

**说明**: 需配合渐变背景使用。CSS 类已内置 `linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)`。

---

### 12. particleFloat — 粒子上浮

| 属性 | 值 |
|------|-----|
| 时长 | 8s |
| 缓动 | ease-in-out |
| 迭代 | infinite |
| 触发条件 | StarBackground 增强 / 庆祝场景 |
| 适用组件 | StarBackground (增强层), ResultScreen (庆祝) |

**关键帧**:
```
0%   → translateY(0) translateX(0), opacity: 0
10%  → opacity: 0.6
90%  → opacity: 0.4
100% → translateY(-100vh) translateX(20px), opacity: 0
```

**说明**: 粒子从底部缓慢上浮到顶部，轻微右偏。适合做「能量上升」的庆祝效果。

---

## 组合用法示例

### 升级场景
```
LevelBadge:  levelUp (0.8s)
XPBar 数字:  numberRoll (0.5s)
背景粒子:    particleFloat (8s, infinite)
```

### 答题正确反馈
```
QuizOptionCard: glowPulse (2s, infinite) — 选中后持续高亮
ToastBar:       fadeIn (0.3s) — 提示「正确！」
```

### 成就领取
```
AchievementPopup: bounceIn (0.5s) — 弹窗出现
Popup 内部:       claimPulse (0.6s) — 脉冲扩散
背景:             particleFloat — 庆祝粒子
```

### 页面切换
```
新页面容器: screenIn (0.4s)
页面内卡片: fadeIn (0.3s, delay 0.1s)
```

---

## 注意事项

1. **性能**: `starPulse` 和 `particleFloat` 使用 `transform` + `opacity`，避免触发 layout。最多 80 颗星同时动画。
2. **prefers-reduced-motion**: 内部团队集成时应添加 media query 禁用 infinite 动画：
   ```css
   @media (prefers-reduced-motion: reduce) {
     .px-anim-starPulse, .px-anim-xSpin, .px-anim-glowPulse,
     .px-anim-shimmer, .px-anim-particleFloat {
       animation: none !important;
     }
   }
   ```
3. **微信 WebView**: `cubic-bezier(0.34, 1.56, 0.64, 1)` 在低性能设备上可能掉帧。建议对 `levelUp` 和 `bounceIn` 添加 `will-change: transform` 属性。
4. **Animation Delay**: 星空粒子的 delay 通过 JS 随机生成（0-4s），不在 CSS 中硬编码。
