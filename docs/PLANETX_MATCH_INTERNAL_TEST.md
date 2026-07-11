# PlanetX「首次星际匹配」内测清单

> **日期**：2026-07-12  
> **对应决策与完整规格**：`/Users/jason/Projects/zervi-genzer/TECH_DOC_PLANETX_MATCH_PHASE1_2026-07-12.md`  
> **契约原文**：`../首次星际匹配_子项目接口契约.md`  
> **范围**：PlanetX 域内闭环；不测信号层 / 终端机 / 链上

---

## 1. 本阶段交付摘要

| 项 | 状态 |
|----|------|
| Hub 不再 toast「即将上线」 | ✅ |
| `POST /v1/game/match` | ✅ |
| 小程序 `pages/match` | ✅ |
| Web `MatchScreen` | ✅ |
| XP 统一为 40 | ✅ |
| 匹配结果落库 | ❌ 延后（不测） |

---

## 2. 自动化

```bash
cd backend
./venv/bin/pytest tests/test_game.py -k match -v
./venv/bin/pytest tests/test_game.py -v   # 建议回归全量游戏用例
```

期望：`test_match_*` 全部 PASSED。

---

## 3. 手工冒烟（双账号）

### 准备

1. 启动后端 `:5200`  
2. 账号 A、B 均完成人格测试  
3. A 建舰队，B 用邀请码加入（舰队 ≥2 人）  
4. A（或 B）在 Hub 确认 `team` 任务已完成（满 3 人会自动 complete；若仅 2 人测匹配 API，Hub 任务锁可能仍锁 match——**产品解锁条件是 `missionsCompleted` 含 `team`**）

> 说明：任务卡片解锁看 `team` 是否完成；匹配 API 只要求「同舰队且另有成员」。内测若要用 UI 点开 match，需先让 `team` 完成（通常 3 人舰队）或本地 store 已标记 team。

### 用例

| ID | 操作 | 通过标准 |
|----|------|----------|
| M1 | 有 team、点「首次星际匹配」 | 进入扫描页，不再 toast |
| M2 | 等待出结果 | 展示双方人格、契合度、理由、舰队名 |
| M3 | A=星云艺术家 配 B=黑洞程序员 | 契合度 **95**，理由含「互补」 |
| M4 | 点确认匹配 | 成就「🎯 首次星际匹配！」；返回 Hub 任务已完成；XP **+40** |
| M5 | 再点该任务 | 提示已完成；服务端不可重复发 XP |
| M6 | 卡片文案 | 显示 `+40 XP · 获得匹配星图`（非 100） |
| M7 | Web 同步走一遍 | 行为与小程序一致 |

### API 直测

```bash
curl -s -X POST http://127.0.0.1:5200/v1/game/match \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{}'

curl -s -X POST http://127.0.0.1:5200/v1/game/mission-complete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mission_id":"match","xp_reward":40}'
```

| 场景 | 期望 `error` |
|------|----------------|
| 无人格 | `personality_required` |
| 无舰队 | `fleet_required` |
| 舰队仅自己 | `fleet_too_small` |

---

## 4. 已知边界（勿报缺陷）

- `/match` **不**自动发 XP；必须前端再调 `mission-complete`  
- 无匹配历史表；刷新后再次匹配为重新计算  
- 不涉及 DemoPPI、信号、链、穿戴  
- Flask 响应里字段名是 `"self"`（实现上用 dict jsonify，避免 kwarg 冲突）

---

## 5. 代码入口（排障）

| 问题 | 先看 |
|------|------|
| 匹配 500 / self 字段 | `backend/src/api/routes/game_routes.py` → `fleet_match` |
| 小程序仍 toast | `frontend/packages/miniprogram/pages/hub/index.ts` |
| Web 点不进去 | `HubScreen.tsx` + `PlanetXHome.tsx` screen=`match` |
| XP 不对 | `MISSION_XP.match` 与 Hub 卡片是否均为 40 |

---

*内测问题请对照完整技术文档 §4 / §5 记录复现步骤。*
