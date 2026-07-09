# 生产架构真源（Production Architecture）

> **版本：** 1.0 · **日期：** 2026-07-09  
> **状态：** ✅ 在线验证通过  
> **维护规则：** 域名 / IP / 反代变更时 **先更新本文档**，再改 Nginx / 构建参数 / 小程序合法域名  
> **关联文档：**  
> - [INTERNAL_TEST_READINESS.md](./INTERNAL_TEST_READINESS.md) — 内测验收  
> - [TENCENT_CLOUD_COMMERCE.md](./TENCENT_CLOUD_COMMERCE.md) — 备案与商业闭环  
> - [DUAL_REPO_WORK_GUIDE.md](./DUAL_REPO_WORK_GUIDE.md) — 双仓分工  
> - [SOCIAL_RINGS_INTEGRATION_RUNBOOK.md](./SOCIAL_RINGS_INTEGRATION_RUNBOOK.md) — 六度同心环联调

---

## 1. 架构总览

```text
用户浏览器 / 小程序
        │
        ├──────────────────────────────────────┐
        │                                      │
        ▼                                      ▼
┌───────────────────────┐            ┌──────────────────────┐
│ 前端机               │            │ API 域名              │
│ 47.115.168.107       │            │ api.genz.ltd          │
│ (备案后 szbolent.cn) │            │ DNS → 1.14.202.161    │
│                      │            │                       │
│ Bolent 门户 SPA  /   │  /v1/ 反代  │ Nginx :80 → :5200     │
│ Nginx 1.24           │ ──────────► │ Looma Flask API       │
└───────────────────────┘            │ 58059 首诗词 + RAG    │
                                     └──────────────────────┘
```

---

## 2. 组件对照表（真源）

| 组件 | 地址 | 状态 | 备注 |
|------|------|------|------|
| **前端门户** | `http://47.115.168.107` | ✅ | Bolent Vue SPA；备案后切换 `szbolent.cn` |
| **前端 Nginx** | `/v1/` → `http://api.genz.ltd/v1/` | ✅ | 门户同源消费 API |
| **API 域名** | `api.genz.ltd` → `1.14.202.161` | ✅ | 小程序 / 直连 API 主入口 |
| **后端 Nginx** | `1.14.202.161:80` → `:5200` | ✅ | gunicorn 仅本机监听 |
| **Looma API** | `1.14.202.161:5200` | ✅ | 58059 首诗词、闭环、社交图谱 |
| **内测直连** | `http://1.14.202.161/` | ✅ | PlanetX / T-space 静态入口 |
| **备案域名（规划）** | `szbolent.cn` / `api.szbolent.cn` | ⬜ | ICP 通过后替换 IP 访问 |

---

## 3. 双机分工

| 机器 | IP | Nginx 版本 | 职责 |
|------|-----|------------|------|
| **前端机** | `47.115.168.107` | 1.24.0 | Bolent 门户静态、`/v1/` 反代至 `api.genz.ltd` |
| **后端机** | `1.14.202.161` | 1.18.0 | Looma API（:5200）、PlanetX / T-space 静态 |

---

## 4. 路由与 DNS

### 4.1 前端机 `47.115.168.107`

| 路径 | 行为 |
|------|------|
| `/` | Bolent 门户 SPA |
| `/v1/*` | 反代 → `http://api.genz.ltd/v1/*` |

### 4.2 后端机 / `api.genz.ltd`

| 路径 | 行为 |
|------|------|
| `/v1/*` | → `127.0.0.1:5200` |
| `/health` | → `:5200/health` |
| `/` | PlanetX SPA（内测） |
| `/tspace/` | T-space SaaS SPA |

### 4.3 DNS

```text
api.genz.ltd     A    1.14.202.161
szbolent.cn      →    47.115.168.107（备案后）
```

---

## 5. 构建与环境变量

| 场景 | API 基址 | 说明 |
|------|----------|------|
| 本地开发 | `http://127.0.0.1:5200` | dev.sh + vite proxy |
| 内测 | `http://api.genz.ltd` | PlanetX / SaaS 构建注入 |
| 门户联调 | `/v1`（同源） | 走前端机反代 |
| 备案后 | `https://api.genz.ltd` | HTTPS + 合法域名 |

**小程序 request 合法域名：** `https://api.genz.ltd`

---

## 6. CORS 配置（待对齐）

当前部分响应仍含 `Access-Control-Allow-Origin: http://1.14.202.161`。

**建议生产 `CORS_ORIGINS`：**

```bash
CORS_ORIGINS=http://1.14.202.161,http://47.115.168.107,http://api.genz.ltd,https://api.genz.ltd,https://szbolent.cn,https://www.szbolent.cn,http://localhost:5173,http://localhost:5174
```

---

## 7. 远端验收记录（2026-07-09）

### 7.1 连通性抽检

| 检查项 | URL | 结果 |
|--------|-----|------|
| 门户首页 | `http://47.115.168.107/` | ✅ HTTP 200 |
| API 健康 | `http://api.genz.ltd/health` | ✅ ok |
| 门户反代 | `http://47.115.168.107/v1/poetry/stats` | ✅ total 58059 |
| 后端直连 | `http://1.14.202.161/health` | ✅ ok |

### 7.2 P0 全量烟雾

```bash
API_BASE=http://api.genz.ltd ./scripts/verify-p0-local.sh
```

| 步骤 | 结果 |
|------|------|
| Health / Compliance / consent | ✅ |
| 闭环 seeker → HR import | ✅ |
| 诗词 58059 首 / 5146 诗人 | ✅ |
| MCP :8999 | ⚠️ 可选未启 |

**结论：** `api.genz.ltd` **已通过 P0 远端验收**。

---

## 8. 运维命令

```bash
API_BASE=http://api.genz.ltd ./scripts/verify-p0-local.sh
API_BASE=http://api.genz.ltd ./scripts/verify-closed-loop.sh
./scripts/verify-deployment.sh api.genz.ltd
curl -sf http://api.genz.ltd/health
```

---

## 9. 与旧文档差异

| 旧写法 | 当前真环境 |
|--------|-----------|
| `api.szbolent.cn` | `api.genz.ltd`（备案前） |
| 单机承载一切 | 前后端分机（§3） |

---

## 10. 变更日志

| 日期 | 变更 |
|------|------|
| 2026-07-09 | 初版：双机架构、api.genz.ltd、P0 远端验收通过 |
