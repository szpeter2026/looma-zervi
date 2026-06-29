# 代码实锤发现与修订记录

> 日期：2026-06-29
> 作者：Jason + WorkBuddy AI 辅助分析
> 目的：记录从原始规划到骨架落地过程中的所有发现、修订和实现决策，供团队成员审议参考

---

## 目录

1. [规划文档验证：6个分歧点逐条实锤](#1-规划文档验证)
2. [额外发现的3个关键问题](#2-额外发现的3个关键问题)
3. [框架骨架评审：5绿1黄](#3-框架骨架评审)
4. [game模块实现：7端点+9CRUD](#4-game模块实现)
5. [2个框架级Bug修复](#5-2个框架级Bug修复)
6. [认证架构决策：Supabase砍掉的逻辑](#6-认证架构决策)
7. [团队分工修正：基于代码实锤](#7-团队分工修正)
8. [下一步行动项](#8-下一步行动项)

---

## 1. 规划文档验证

### 1.1 双认证比文档描述更复杂

**文档原描述**：PlanetX用Supabase JWT；T空间用looma token → 2个认证入口

**代码实锤**：实际上是**4个认证入口**：

| 入口 | 路径 | 文件位置 | 说明 |
|------|------|----------|------|
| Supabase注册 | POST /register-supabase | auth_routes.py L142 | 邮箱+密码→Supabase UID |
| Supabase登录 | POST /login-supabase | auth_routes.py L218 | 邮箱+密码→Supabase JWT |
| looma注册 | POST /v1/auth/register | auth_routes.py L25 | 邮箱+密码→SQLite user |
| looma登录 | POST /v1/auth/login | auth_routes.py L68 | 邮箱+密码→token-xxx |

**影响**：同一用户在PlanetX注册后，在T空间Panel登录完全是另一个人（不同数据库、不同ID体系）。这不是"以后可以优化"的问题，是转化链路从根上断了。

### 1.2 /v1/auth/sync 语义冲突

**文档规划**：POST /v1/auth/sync 是"Supabase JWT → looma token"的桥接

**代码实锤**：当前 /v1/auth/sync 做的是**反向**——looma往Supabase写数据（profiles + 邀请码消费），位于 auth_routes.py L321-403。

**修订建议（已被骨架采纳）**：
- 旧语义 → 重命名为 `/v1/auth/supabase-onboard`（保留给后续迁移兼容）
- 新桥接 → `/v1/auth/bridge`（Supabase JWT → looma token）
- 骨架决策：直接砍掉Supabase，bridge端点保留但返回501（后续需要Google/GitHub社交登录时再接）

### 1.3 /v1/game/* 路由从零开发

**文档描述**：Phase 2 需要新增7个game端点

**代码实锤**：app.py L56 无 game_router，routes/ 无 game.py。这不是"适配"，是从零开发一整套REST API。

**修订**：
- 时间线从24天→26-37天（5-7周）
- 优先只做 personality_result + profile_sync，舰队和任务后续迭代
- 骨架已有game_routes.py蓝图注册，7个端点骨架+TODO占位

**本次实现状态**：7个端点已全部填充真实实现（见第4节）

### 1.4 DNSPod拦截问题

**文档描述**：GET+Bearer被DNSPod 302拦截

**代码实锤**：CORS是 `allow_origins=["*"]`，问题不在后端CORS层，而在上游CDN/WAF。

**修订建议**：
- 优先排查Cloudflare/腾讯云WAF Rules
- 短期workaround：GET profile/quota 改POST
- 长期方案：api.genz.ltd CDN安全级别调整

### 1.5 shared包拆分不够激进

**文档描述**：拆成 createPlanetXApi() + createSaasApi()

**代码实锤**：shared/endpoints.ts 聚合导出含 auth/chat/docs/resume/jobs/reports/system/referral 所有模块，PlanetX引入时打包进saas的docs/resume/reports。

**修订建议**：分阶段——先删聚合导出 `createApi()`，比拆3包更务实
**骨架决策**：拆为 shared-core（类型+ApiClient+常量），planetx/saas各自组合API端点，index.ts明确标注"双审"

### 1.6 时间线过于乐观

| 阶段 | 文档估算 | 修订建议 | 依据 |
|------|----------|----------|------|
| Phase 1 拆包 | 3-5天 | 5-7天 | CSS隔离+路由重配+Vite+CI/CD边缘问题多 |
| Phase 2 认证+游戏 | 5-7天 | 10-14天 | game路由从零开发，auth桥接涉及JWT验证改造 |
| Phase 3 转化链路 | 3-5天 | 5-7天 | 支付+裂变+HR画像 |
| Phase 4 SaaS完整 | 5-7天 | 7-10天 | Enterprise面板全新功能 |
| **总计** | **24天** | **26-37天(5-7周)** | |

---

## 2. 额外发现的3个关键问题

### 2.1 ⚠️ AUTH_STUB=true 是生产级安全漏洞

**代码位置**：auth.py L156

```python
AUTH_STUB = os.getenv("AUTH_STUB", "true")  # 默认是 true！
```

**后果**：任何邮箱 + 任何密码都能成功登录并获得有效token。比所有功能规划都紧急。

**骨架修复**：AUTH_STUB 已从新代码中移除，改用真实JWT验证（jwt_handler.py）。

### 2.2 Token不是JWT，无过期机制

**代码位置**：auth_routes.py L51

```python
token = f"token-{user_id[:8]}"  # 不是JWT！
```

响应声称 `expires_in=3600`，但验证代码完全不检查过期。一旦发出去永远有效。

**骨架修复**：jwt_handler.py 实现了完整的 sign/verify/exp 机制，token格式改为标准JWT。

### 2.3 users表缺少supabase_uid字段

**代码位置**：manager.py L58-66

```python
# 旧表只有：id, email, password_hash, tier, created_at
# 没有 supabase_uid → looma完全不知道Supabase用户是谁
```

**影响**：/v1/auth/bridge 无法建立映射关系。

**骨架修复**：新DB schema 加了 `wechat_openid` 字段（小程序认证需要），supabase_uid 因砍掉Supabase决策而不再需要，但留了 `auth_provider` 字段做未来扩展。

---

## 3. 框架骨架评审

### 评审结果：5绿1黄，整体接受

#### 后端（5绿1黄）

| 项目 | 结论 | 说明 |
|------|------|------|
| AUTH_STUB删除→真实JWT | ✅ | jwt_handler.py 实现了sign/verify/exp，P0安全漏洞彻底修复 |
| 9个路由蓝图全部注册 | ✅ | 含/v1/game/*，骨架已有 |
| DB Schema 9张表+wechat_openid | ✅ | 完全符合规划，ownership注释写进去了 |
| Supabase移除 | ✅ | auth-architecture-decision.md(347行)，逻辑自洽 |
| 微信小程序认证路径 | ✅ | wechat_auth.py + code2session + openid→looma JWT |
| game fleet/mission DB操作 | ⚠️ | TODO占位→**现已实现（本次commit）** |

#### 前端（5绿）

| 项目 | 结论 | 说明 |
|------|------|------|
| 按品牌拆分4包 | ✅ | shared-core / planetx / saas / miniprogram |
| CSS Token物理隔离 | ✅ | --px-*（深空游戏）vs --color-*（商务浅色），命名空间不冲突 |
| AuthGuard品牌独立 | ✅ | PlanetXAuthGuard vs SaasAuthGuard 分离 |
| shared-core契约化 | ✅ | 只导出类型/ApiClient/常量，双审注释 |
| 小程序壳+CloudBase | ✅ | 轻量接入层定位 |

---

## 4. game模块实现

### 4.1 manager.py 新增9个CRUD方法

| 方法 | 功能 | 关键设计 |
|------|------|----------|
| `fleet_create()` | 创建舰队 | UNIQUE(name)防重名，captain自动加入 |
| `fleet_get()` | 查询舰队详情 | 含member列表+captain信息 |
| `fleet_join()` | 加入舰队 | 查重：已在某舰队→409 |
| `fleet_leave()` | 离开舰队 | 船长不能离→403，必须dissolve |
| `fleet_dissolve()` | 解散舰队 | 只有captain能操作 |
| `mission_complete()` | 完成任务 | UNIQUE(user_id,mission_id)防双刷→409 |
| `mission_get()` | 查询任务 | 返回mission详情+奖励XP |
| `mission_check_double()` | 检查重复完成 | 前端预检查用 |
| `update_level()` | 等级计算 | `level = floor(sqrt(xp/100)) + 1`，自然减速曲线 |

### 4.2 game_routes.py 7个端点实现

| 端点 | Method | 功能 | 认证 | 状态码 |
|------|--------|------|------|--------|
| `/profile/sync` | POST | 同步人格测试结果 | JWT | 200/404 |
| `/profile/{user_id}` | GET | 查询游戏档案 | JWT | 200 |
| `/mission/complete` | POST | 完成任务+XP | JWT | 200/409 |
| `/fleet/create` | POST | 创建舰队 | JWT | 201/409 |
| `/fleet/{fleet_id}` | GET | 查询舰队 | JWT | 200/404 |
| `/fleet/join` | POST | 加入舰队 | JWT | 200/409/403 |
| `/fleet/leave` | POST | 离开舰队 | JWT | 200/403 |

### 4.3 关键设计决策

- **一人一舰队**：MVP阶段限制，已在舰队的人创建/加入另一舰队→409
- **船长不能离开**：必须dissolve整个舰队→403，避免"船长跑了舰队无人管"
- **Mission双刷防护**：DB UNIQUE约束 + API层409返回
- **XP→Level自动计算**：`floor(sqrt(xp/100)) + 1`，100XP→Lv2, 400XP→Lv3, 900XP→Lv4
- **Mission自动创建stub profile**：没做过人格测试的用户也能完成mission（自动建空profile）

---

## 5. 2个框架级Bug修复

### 5.1 Config类属性缓存Bug

**根因**：

```python
# config.py（旧版）
class Config:
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/looma.db")  # import时计算！
```

Python类属性在 `class` 定义时（即import时）就计算了。后续 `os.environ["DATABASE_PATH"] = "new_path"` 不影响 `Config.DATABASE_PATH`。

**后果**：pytest测试间DB文件污染——第1个测试的DB路径被缓存，后续测试都写入同一个文件，导致"email已存在"错误。

**修复**：

```python
# config.py（新版）
def _refresh_config():
    """Re-read env vars into Config class attributes.
    Called by create_app() so Flask picks up runtime env changes."""
    Config.DATABASE_PATH = os.getenv("DATABASE_PATH", "data/looma.db")
    Config.JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    Config.SECRET_KEY = os.getenv("SECRET_KEY", "dev-flask-secret")
    # ... all other env-driven attributes
```

**app.py调用**：

```python
def create_app(env="development"):
    app = Flask(__name__)
    _refresh_config()  # ← 每次创建app时重读env
    app.config.from_object(Config)
```

### 5.2 :memory: SQLite DB不持久Bug

**根因**：SQLite `:memory:` 模式下，每个连接都是独立的空DB。`DatabaseManager.get_conn()` 每次创建新连接→schema创建后连接关闭→表消失。

**修复**：`DatabaseManager.__init__()` 检测 `:memory:` 并改为URI格式共享：

```python
def __init__(self, db_path: str):
    if db_path == ":memory:":
        # URI format allows shared in-memory DB across connections
        self.db_path = "file:memdb?mode=memory&cache=shared"
        self._uri_mode = True
    else:
        self.db_path = db_path
        self._uri_mode = False
```

**测试层面**：test_auth.py 和 test_game.py 改用 `tempfile.NamedTemporaryFile(suffix='.db')` 替代 `:memory:`，更可靠。

---

## 6. 认证架构决策

### 6.1 Supabase砍掉的决策逻辑

**原规划**：Supabase降级为JWT签发器，通过 `/v1/auth/bridge` 桥接

**骨架决策**：Web端用looma自签JWT（bcrypt+PyJWT），小程序端用openid→looma JWT，Supabase完全退场

**决策依据**（见 docs/auth-architecture-decision.md）：

| 保留Supabase的理由 | MVP阶段是否必要 | 替代方案 |
|---------------------|:---:|----------|
| 邮箱验证 | ❌ | 自建：注册时发确认邮件（Phase4后） |
| 密码重置 | ❌ | 自建：token-based重置链接 |
| 社交登录(Google/GitHub) | ❌ | `/v1/auth/bridge` 留501占位 |
| JWT签发 | ❌ | PyJWT自签，更简单 |
| anon key前端安全风险 | 🔴 | 砍掉即消除 |

**结论**：砍掉后认证链路更短，调试复杂度降低，前端不再暴露Supabase anon key。`/v1/auth/bridge` 留着但返回501，后续需要社交登录时再接。

### 6.2 新认证流程

```
Web端: 邮箱+密码 → bcrypt验证 → PyJWT签发 → looma JWT token
小程序: wx.login() → code2session → openid → looma JWT token
未来社交: Google/GitHub OAuth → /v1/auth/bridge(501) → 按需实现
```

---

## 7. 团队分工修正

### 7.1 原方案 vs 修正方案

**原方案**：Jason own PlanetX前端，szbenyx own SaaS前端

**代码实锤推翻**：

```
Jason:  38 Python文件改动, 0 前端TS/TSX改动 → 纯后端
szbenyx: 109 Python + 113 TS/TSX + 7 Rust → 全栈
```

让纯Python开发者独自交付7个React页面 + CSS + Store + AuthGuard = 交付风险极高。

**修正方案**：

| 层 | Jason | szbenyx | AI补位 |
|---|---|---|---|
| **核心能力区** | 后端auth/game/agents全自力 | SaaS前端+后端+CI全自力 | 审查辅助 |
| **AI补位区** | PlanetX前端—Jason出设计意图，AI出代码 | — | 主力交付 |
| **协同区** | 定义产品边界+数据流 | shared-core架构+双审 | 桥接代码 |

**Jason的PlanetX前端交付模式**：Jason设计交互流程 → AI生成React代码 → Jason审查确认 → szbenyx双审shared-core改动

### 7.2 修正后Phase分工

| Phase | Jason主抓 | szbenyx主抓 | 联合 |
|-------|-----------|-------------|------|
| Phase 0 产品边界 | ✅ 需求梳理+功能矩阵 | ✅ 技术约束评估 | — |
| Phase 1 拆包 | 后端结构对齐 | **前端骨架搭建**(他搭过Monorepo) | shared-core双审 |
| Phase 2 认证+游戏 | **auth bridge + game API**(本次已交付game) | SaaS端auth切换+前端适配 | DB schema对齐 |
| Phase 3 转化链路 | 后端支付+裂变逻辑 | HR画像页+支付前端 | — |
| Phase 4 SaaS完整 | agents/pipeline微调 | Enterprise面板 | — |

---

## 8. 下一步行动项

### 8.1 P0 本周必须做

| # | 事项 | 负责人 | 状态 |
|---|------|--------|------|
| 1 | AUTH_STUB=false 生产环境设置 | szbenyx | 骨架已修复（移除AUTH_STUB） |
| 2 | DNSPod拦截排查 | Jason | 待排查 |
| 3 | /v1/auth/sync 重命名 | szbenyx | 骨架已处理（Supabase退场） |
| 4 | users表加扩展字段 | szbenyx | 骨架已加wechat_openid+auth_provider |
| 5 | Phase0矩阵签字 | Jason+szbenyx | **待做** |

### 8.2 P1 1-2周内

| # | 事项 | 负责人 | 依赖 |
|---|------|--------|------|
| 6 | 旧web包7个planetx页面迁移到packages/planetx | szbenyx | Phase0矩阵签字 |
| 7 | 认证统一最小方案验证 | Jason | game_routes已实现，待前端适配 |
| 8 | 前端拆包独立dev运行 | szbenyx | 旧页面迁移 |

### 8.3 已完成

| # | 事项 | 交付 |
|---|------|------|
| ✅ | manager.py fleet/mission CRUD | 9个方法，+224行 |
| ✅ | game_routes.py 7端点实现 | +186行，含/fleet/leave新端点 |
| ✅ | Config缓存bug修复 | _refresh_config()机制 |
| ✅ | :memory: DB bug修复 | URI共享模式+tempfile测试 |
| ✅ | 26个game测试 | 34个全部pass，0 failure |
| ✅ | ruff lint | clean |

---

## 附录A：测试覆盖详情

```
test_game.py 26个测试:
  - test_sync_personality: 人格结果同步(正常+404未找到)
  - test_get_game_profile: 查询游戏档案
  - test_mission_complete: 完成任务(正常+409双刷)
  - test_mission_check_double: 预检查重复
  - test_fleet_create: 创建舰队(正常+409重名+409已在舰队)
  - test_fleet_get: 查询舰队(正常+404不存在)
  - test_fleet_join: 加入舰队(正常+409已在+404不存在)
  - test_fleet_leave: 离开(正常+403船长不能离)

test_auth.py 8个测试:
  - test_register_and_login: 注册+登录流程
  - test_duplicate_registration: 重复邮箱409
  - test_login_wrong_password: 错误密码401
  - test_profile_with_token: token认证查询profile
  - test_profile_without_token: 无token401
  - test_invalid_token: 假token401
  - test_update_profile: 更新用户信息
  - test_register_missing_fields: 缺字段400

合计: 34 passed, 0 failed
```

## 附录B：文件变更清单

```
修改:
  backend/src/db/manager.py       +224行 (9个CRUD方法 + :memory: URI支持)
  backend/src/api/routes/game_routes.py  +186行 (7端点TODO→真实实现)
  backend/src/config.py           +41行 (_refresh_config机制)
  backend/src/app.py              +2行 (调用_refresh_config)
  backend/tests/test_auth.py      +17行 (tempfile替代:memory:)

新增:
  backend/tests/test_game.py      +459行 (26个测试全覆盖)
```
