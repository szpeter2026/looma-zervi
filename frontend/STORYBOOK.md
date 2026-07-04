# looma-zervi Phase 3 — Storybook 验收环境

> **用途：** PlanetX + SaaS 共 22 个纯 UI 组件 · CSF Stories 走查 · 外包 Phase 3 签收  
> **端口：** `6007`（与 szbolent-portal Storybook `:6006` 错开）

---

## 启动

```bash
cd frontend
pnpm install
pnpm storybook
```

浏览器打开 **http://localhost:6007**。

静态构建（CI / 外包交付包）：

```bash
pnpm build-storybook
# 输出 storybook-static/
```

---

## 目录

| 路径 | 说明 |
|------|------|
| `.storybook/main.ts` | 扫描 `packages/*/src/**/*.stories.tsx` |
| `.storybook/preview.tsx` | 双品牌 tokens + 按 title 切换画布背景 |
| `packages/planetx/src/brand/ui/stories/` | PlanetX 10 组件 Stories |
| `packages/saas/src/brand/ui/stories/` | SaaS 12 组件 Stories |
| `ui-preview.html` | 无 Storybook 时的静态 HTML 预览（备用） |

---

## Phase 3 交付清单

| # | 交付物 | 状态 | 文件 |
|---|--------|------|------|
| 1 | PlanetX Design Tokens (36→85+) | ✅ | `planetx/src/brand/tokens.css` |
| 2 | SaaS Design Tokens (55→110+) | ✅ | `saas/src/brand/tokens.css` |
| 3 | PlanetX 动画 (5→12 keyframe + 工具类) | ✅ | `planetx/src/brand/animations.css` |
| 4 | 动画规格书 | ✅ | `planetx/src/brand/ANIMATION_SPEC.md` |
| 5 | PlanetX 10 个纯 UI 组件 | ✅ | `planetx/src/brand/ui/` |
| 6 | SaaS 12 个纯 UI 组件 | ✅ | `saas/src/brand/ui/` |
| 7 | Storybook Stories (CSF) | ✅ | `*/ui/stories/*.stories.tsx` |
| 8 | HTML 预览页面 | ✅ | `ui-preview.html` |
| 9 | **Storybook 运行环境** | ✅ | `frontend/.storybook/` + `pnpm storybook` |

---

## 验收走查

1. 左侧 **PlanetX/** 与 **SaaS/** 分组下所有 Story 可渲染  
2. 每个组件至少覆盖：默认 / 变体 / disabled 或 loading（见各 `.stories.tsx`）  
3. PlanetX 动画类（`px-anim-*`）在 Story 中可见  
4. `pnpm typecheck`（各 package）零错误  

---

## 与 portal Storybook 的分工

| 仓 | 框架 | 用途 |
|----|------|------|
| **looma-zervi/frontend** | React · Phase 3 组件库 | 产品 UI 外包验收 |
| **szbolent-portal** | Vue 3 · 过渡组件 | 门户 Vue 壳（Astra 迁移后弱化） |
