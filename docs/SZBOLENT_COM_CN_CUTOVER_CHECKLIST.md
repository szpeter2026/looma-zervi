# szbolent.com.cn 双机切换清单（DNS + Nginx + 环境变量）

> **版本：** 1.0 · **日期：** 2026-07-11  
> **用途：** 从当前内测态（`api.genz.ltd` + IP）迁移到企业备案主域 `szbolent.com.cn`  
> **同步副本：** `szbolent-portal/docs/SZBOLENT_COM_CN_CUTOVER_CHECKLIST.md`（须同文同版）  
> **关联：** [PRODUCTION_ARCHITECTURE.md](./PRODUCTION_ARCHITECTURE.md) · [TENCENT_CLOUD_COMMERCE.md](./TENCENT_CLOUD_COMMERCE.md)（portal 仓）

---

## 0. 迁移总览

### 0.1 现状 → 目标

| 项 | 现状（内测） | 目标（企业商业主域） |
|----|-------------|---------------------|
| 门户入口 | `http://47.115.168.107` | `https://www.szbolent.com.cn` |
| API 入口 | `http://api.genz.ltd` | `https://api.szbolent.com.cn` |
| 门户机 | `47.115.168.107` | 不变 |
| 后端机 | `1.14.202.161` | 不变 |
| PlanetX / T-space | `http://1.14.202.161/`、`/tspace/` | 可保留 IP 内测；商业流量走 `.com.cn` |
| 小程序合法域名 | `api.genz.ltd`（规划） | **`api.szbolent.com.cn`** |
| 备案主体 | 个人 `szbolent.cn` / `genz.ltd`；企业 `szbolent.com.cn` | **商业只走企业域** |

### 0.2 双机架构（切换后）

```text
用户 / 小程序
    │
    ├─ https://www.szbolent.com.cn ──► 47.115.168.107（szbolent-portal SPA）
    │         /v1/* 反代 ──────────────────► https://api.szbolent.com.cn/v1/*
    │
    └─ https://api.szbolent.com.cn ──► 1.14.202.161 Nginx :443 → Looma :5200

辅助（过渡期可保留，非商业主域）：
    api.genz.ltd ──► 1.14.202.161（301 或并行）
    szbolent.cn ──► 301 → www.szbolent.com.cn
    1.14.202.161/、/tspace/ ──► PlanetX / SaaS 内测
```

### 0.3 执行原则

1. **先 DNS + HTTP 验证，再上 HTTPS**（避免 certbot 失败）
2. **先 API 域 `api.szbolent.com.cn`，再门户 `www`**（小程序依赖 API）
3. **`api.genz.ltd` 保留 2～4 周并行**，确认无流量后再 301
4. **个人 `szbolent.cn` 不做商业入口**，仅 301 或展示页
5. **门户不走 looma-zervi CI**，需单独 build + 部署

---

## 1. 前置确认（Day 0）

### 1.1 备案与主体

- [ ] `szbolent.com.cn` 企业 ICP 备案 **已通过**
- [ ] 企业备案材料中 **首页 URL** 为 `https://www.szbolent.com.cn`（或可先 HTTP 再改）
- [ ] **`api.szbolent.com.cn` 已作为同一企业备案的二级域名**（未备则先在腾讯云补备）
- [ ] 备案主体 = 后续微信支付商户号主体 = 小程序企业认证主体
- [ ] 公安联网备案（ICP 通过后 30 日内）

### 1.2 服务器与端口

| 机器 | IP | 开放端口 | 角色 |
|------|-----|----------|------|
| 前端机 | `47.115.168.107` | 80、443 | szbolent-portal |
| 后端机 | `1.14.202.161` | 80、443 | Looma API + PlanetX/T-space |

- [ ] 两台机 `ufw`/安全组已放行 **80、443**
- [ ] 后端 Looma 仍监听 `127.0.0.1:5200`（Docker gunicorn）

### 1.3 域名注册

- [ ] `szbolent.com.cn` 在腾讯云（或与备案同一服务商）
- [ ] 有 DNS 解析权限（添加 A 记录）

---

## 2. DNS 配置

在域名 DNS 控制台添加（TTL 建议 600s，便于回滚）：

### 2.1 企业主域（必做）

| 记录类型 | 主机记录 | 记录值 | 说明 |
|----------|----------|--------|------|
| A | `www` | `47.115.168.107` | 门户 canonical |
| A | `@` | `47.115.168.107` | 根域（Nginx 301 → www） |
| A | `api` | `1.14.202.161` | Looma API |

### 2.2 可选（P1+）

| 记录类型 | 主机记录 | 记录值 | 说明 |
|----------|----------|--------|------|
| A | `cms` | `1.14.202.161` 或 WP 机 | WordPress headless |
| A | `m` | `47.115.168.107` | 小程序 H5（按需） |

### 2.3 过渡期保留（勿删，并行验证）

| 记录 | 现状 | 切换后策略 |
|------|------|------------|
| `api.genz.ltd` | → `1.14.202.161` | 保留 2～4 周，后改 301 → `api.szbolent.com.cn` |
| `szbolent.cn` / `www.szbolent.cn` | 个人备案 | 301 → `www.szbolent.com.cn`（见 §4.5） |

### 2.4 DNS 验证命令

```bash
dig +short www.szbolent.com.cn
dig +short api.szbolent.com.cn
dig +short szbolent.com.cn

# 期望：
# www / @ → 47.115.168.107
# api     → 1.14.202.161
```

- [ ] 本机 `dig` 结果正确
- [ ] 手机 4G 网络 `dig` 结果正确（排除本地 DNS 缓存）

---

## 3. SSL 证书（DV 免费即可）

两台机器各自申请（Let's Encrypt 或腾讯云免费 DV）。

### 3.1 后端机 `1.14.202.161`

```bash
sudo apt update && sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --nginx -d api.szbolent.com.cn
```

证书路径：`/etc/letsencrypt/live/api.szbolent.com.cn/fullchain.pem`

- [ ] 证书签发成功
- [ ] `sudo certbot renew --dry-run` 通过

### 3.2 前端机 `47.115.168.107`

```bash
sudo certbot certonly --nginx -d szbolent.com.cn -d www.szbolent.com.cn
```

- [ ] 门户证书签发成功

### 3.3 可选

`genz.ltd`、`api.genz.ltd` 若继续用，单独续签，**不与 `.com.cn` 混商户号**。

---

## 4. Nginx 配置

### 4.1 后端机 `1.14.202.161` — API 专域

**新建** `/etc/nginx/sites-available/api.szbolent.com.cn`（对照现状：原 `nginx-api.genz.ltd.conf`）：

```nginx
server {
    listen 80;
    server_name api.szbolent.com.cn;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.szbolent.com.cn;

    ssl_certificate     /etc/letsencrypt/live/api.szbolent.com.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.szbolent.com.cn/privkey.pem;

    client_max_body_size 20m;

    location /v1/ {
        proxy_pass http://127.0.0.1:5200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_buffering off;
    }

    location /api/ {
        rewrite ^/api/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:5200;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    location = /health {
        proxy_pass http://127.0.0.1:5200/health;
        proxy_set_header Host $host;
        access_log off;
    }

    location / {
        return 404;
    }
}
```

```bash
sudo ln -sf /etc/nginx/sites-available/api.szbolent.com.cn /etc/nginx/sites-enabled/
sudo nginx -t && sudo nginx -s reload
```

- [ ] `curl -sf https://api.szbolent.com.cn/health`
- [ ] `curl -sf "https://api.szbolent.com.cn/v1/poetry/random?count=1"`

### 4.2 后端机 — PlanetX / T-space（内测）

`nginx-looma-zervi-ip.conf` 继续服务 `/`、`/tspace/`。GitHub `DEPLOY_NGINX_MODE=ip` 与 API 专域 **共存**。

### 4.3 后端机 — `api.genz.ltd` 过渡期

并行 2 周后：

```nginx
server {
    listen 80;
    server_name api.genz.ltd;
    return 301 https://api.szbolent.com.cn$request_uri;
}
```

### 4.4 前端机 `47.115.168.107` — 门户

**替换** `szbolent-portal/nginx.conf`（对照现状：当前 `/v1/` → `http://api.genz.ltd/v1/`）：

```nginx
server {
    listen 80;
    server_name szbolent.com.cn;
    return 301 https://www.szbolent.com.cn$request_uri;
}

server {
    listen 443 ssl http2;
    server_name szbolent.com.cn;
    ssl_certificate     /etc/letsencrypt/live/szbolent.com.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/szbolent.com.cn/privkey.pem;
    return 301 https://www.szbolent.com.cn$request_uri;
}

server {
    listen 80;
    server_name www.szbolent.com.cn;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.szbolent.com.cn;

    ssl_certificate     /etc/letsencrypt/live/szbolent.com.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/szbolent.com.cn/privkey.pem;

    root /var/www/szbolent-portal/dist;
    index index.html;
    charset utf-8;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml image/svg+xml;
    gzip_min_length 256;
    gzip_vary on;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /v1/ {
        proxy_pass https://api.szbolent.com.cn/v1/;
        proxy_set_header Host api.szbolent.com.cn;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_server_name on;
        proxy_connect_timeout 10s;
        proxy_read_timeout 120s;
        proxy_send_timeout 10s;
    }
}
```

- [ ] `curl -sfI https://www.szbolent.com.cn | head -1`

### 4.5 个人 `szbolent.cn` 降级

```nginx
server {
    listen 80;
    server_name szbolent.cn www.szbolent.cn;
    return 301 https://www.szbolent.com.cn$request_uri;
}
```

- [ ] 个人域不再承载支付、会员、企业小程序入口

---

## 5. 环境变量切换

### 5.1 后端 `.env`（`1.14.202.161:/opt/looma-zervi/backend/.env`，**CI 不会自动写**）

```bash
CORS_ORIGINS=https://szbolent.com.cn,https://www.szbolent.com.cn,https://api.szbolent.com.cn,https://api.genz.ltd,http://1.14.202.161,http://47.115.168.107,http://localhost:5173,http://localhost:5174,http://localhost:3000
```

支付 P1 追加：

```bash
WECHAT_PAY_NOTIFY_URL=https://api.szbolent.com.cn/v1/payment/notify/wechat
```

```bash
cd /opt/looma-zervi/docker && docker compose -p looma-zervi restart
```

### 5.2 looma-zervi `.github/workflows/deploy.yml`

```yaml
      - name: Build PlanetX
        env:
          VITE_API_BASE: "https://api.szbolent.com.cn"
          VITE_SAAS_URL: "/tspace/"

      - name: Build Saas (T-space)
        env:
          VITE_API_BASE: "https://api.szbolent.com.cn"
```

GitHub Variable：`DEPLOY_NGINX_MODE = ip`

### 5.3 szbolent-portal `.env.production`（对照现状：`VITE_SITE_URL=http://47.115.168.107`）

```env
VITE_SITE_URL=https://www.szbolent.com.cn
VITE_LOOMA_API_BASE=https://api.szbolent.com.cn
VITE_BLOG_API_BASE=https://cms.szbolent.com.cn/wp-json/wp/v2
VITE_TATHA_POETRY_ENABLED=false
```

或同源模式（`VITE_LOOMA_API_BASE` 留空，走 §4.4 `/v1/` 反代）。

```bash
cd szbolent-portal && npm ci && npm run build
rsync -avz dist/ ubuntu@47.115.168.107:/var/www/szbolent-portal/dist/
```

### 5.4 微信小程序 `frontend/packages/miniprogram/utils/config.ts`

```typescript
export const API_BASE = 'https://api.szbolent.com.cn'
```

### 5.5 微信公众平台

| 配置项 | 值 |
|--------|-----|
| request 合法域名 | `https://api.szbolent.com.cn` |
| uploadFile | `https://api.szbolent.com.cn` |
| downloadFile | `https://api.szbolent.com.cn` |
| 业务域名（H5） | `https://www.szbolent.com.cn` |

---

## 6. 从 `api.genz.ltd` 迁移（四阶段）

### Phase 1 — API 切域

| 步骤 | 操作 | 验收 |
|------|------|------|
| 1.1 | DNS `api` → `1.14.202.161` | `dig` 正确 |
| 1.2 | §4.1 Nginx + SSL | `curl https://api.szbolent.com.cn/health` |
| 1.3 | `backend/.env` CORS | OPTIONS 预检通过 |
| 1.4 | 小程序 config + 合法域名 | 体验版登录成功 |
| 1.5 | `API_BASE=https://api.szbolent.com.cn ./scripts/verify-p0-local.sh` | 全绿 |

### Phase 2 — 门户切域

| 步骤 | 操作 | 验收 |
|------|------|------|
| 2.1 | DNS `www` / `@` → `47.115.168.107` | `dig` 正确 |
| 2.2 | §4.4 Nginx + SSL | `https://www.szbolent.com.cn` 200 |
| 2.3 | portal build + rsync | 诗词 / 登录正常 |
| 2.4 | 浏览器 Network 无 CORS 错误 | — |

### Phase 3 — 收敛旧域

| 步骤 | 操作 |
|------|------|
| 3.1 | `szbolent.cn` 301 → `www.szbolent.com.cn` |
| 3.2 | 监控 `api.genz.ltd` 2 周 |
| 3.3 | `api.genz.ltd` 301 → `api.szbolent.com.cn` |
| 3.4 | 更新 `PRODUCTION_ARCHITECTURE.md`、`quick_smoke_test.sh` |

### Phase 4 — 支付 P1

| 步骤 | 操作 |
|------|------|
| 4.1 | 微信支付商户号（大陆子公司） |
| 4.2 | 回调 `https://api.szbolent.com.cn/v1/payment/notify/wechat` |
| 4.3 | `PAYMENT_STUB_MODE=false` + 0.01 元实单 |

---

## 7. 验收命令（Done 标准）

```bash
curl -sf https://api.szbolent.com.cn/health
curl -sf "https://api.szbolent.com.cn/v1/poetry/random?count=1"
curl -sf "https://api.szbolent.com.cn/v1/poetry/stats"
curl -sfI https://www.szbolent.com.cn | head -3
curl -sfI https://szbolent.com.cn | grep -i location

API_BASE=https://api.szbolent.com.cn ./scripts/verify-p0-local.sh
API_BASE=https://api.szbolent.com.cn ./scripts/verify-closed-loop.sh
./scripts/verify-deployment.sh api.szbolent.com.cn

curl -sI -X OPTIONS "https://api.szbolent.com.cn/v1/auth/me" \
  -H "Origin: https://www.szbolent.com.cn" \
  -H "Access-Control-Request-Method: GET" | grep -i access-control
```

**Done：**

- [ ] 以上命令全部通过
- [ ] 小程序体验版（登录 → 诗词 → Ask consent）通过
- [ ] 门户 Pricing 能拉 `/v1/payment/plans`
- [ ] `api.genz.ltd` 已 301 或文档标明弃用日期

---

## 8. 回滚方案

| 故障 | 回滚 |
|------|------|
| API 新域不通 | DNS 回滚；小程序合法域改回 `api.genz.ltd` |
| 门户 HTTPS 失败 | 临时 `http://47.115.168.107` |
| CORS 错误 | 查 `backend/.env` CORS_ORIGINS；重启 Docker |
| 支付回调失败 | 商户平台回调 URL 改回旧域 |

保留 **7 天** IP + `api.genz.ltd` 并行，再执行 Phase 3。

---

## 9. 文件变更对照表

| 文件 | 机器/仓 | 变更 |
|------|---------|------|
| DNS 控制台 | 腾讯云 | `www`、`api` A 记录 |
| `/etc/nginx/sites-available/api.szbolent.com.cn` | `1.14.202.161` | **新建** |
| `/opt/looma-zervi/backend/.env` | `1.14.202.161` | CORS、支付回调 |
| `szbolent-portal/nginx.conf` | `47.115.168.107` | 替换 §4.4 |
| `szbolent-portal/.env.production` | 构建机 | §5.3 |
| `.github/workflows/deploy.yml` | looma-zervi | `VITE_API_BASE` |
| `frontend/packages/miniprogram/utils/config.ts` | looma-zervi | `API_BASE` |
| `scripts/quick_smoke_test.sh` 等 | looma-zervi | 域名更新 |
| 微信公众平台 | 控制台 | 合法域名 |

**不在此次范围：** `genz.ltd` 叙事线、`cms.szbolent.com.cn`（P1+）、SaaS `BrowserRouter basename="/tspace"`。

---

## 10. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-07-11 | 初版：双机 DNS/Nginx/环境变量 + api.genz.ltd 迁移四阶段 |
