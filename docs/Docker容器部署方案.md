# Looma Docker 容器部署方案

> 状态：待团队研判  
> 日期：2026-06-30

---

## 1. 方案概述

### 核心思路

| 阶段 | 方式 | 频率 |
|------|------|------|
| **Docker 镜像部署** | 手动 SSH 到服务器执行 `docker compose up --build` | 仅首次 / 依赖变更时 |
| **代码部署** | GitHub Actions CI/CD 自动 rsync + restart | 每次 push main |

Docker 镜像只在首次手动构建一次，后续 CI 只同步代码 + 重启容器（代码通过 volume 挂载，无需 rebuild）。

---

## 2. 容器架构

```
                    ┌──────────────┐
                    │    Nginx     │  :80 / :443
                    │ nginx:alpine │
                    └──┬───┬───┬──┘
                       │   │   │
          ┌────────────┼───┤   └──────────────┐
          │            │   │                  │
     api.genz.ltd  planetx  t.genz.ltd
          │         .genz.ltd     │
          ▼            ▼          ▼
   ┌──────────┐  /var/www/   /var/www/
   │ Backend  │  planetx/    saas/
   │ Flask    │  dist/       dist/
   │ :5000    │
   └────┬─────┘
        │
        ▼
   ┌──────────┐
   │ ChromaDB │  :8000
   │ (向量库)  │
   └──────────┘
```

### 三个容器

| 容器 | 镜像 | 端口 | 构建方式 |
|------|------|------|----------|
| **backend** | `Dockerfile.backend` → Python 3.12 + Gunicorn | 5000 | 手动 `docker compose build` |
| **chromadb** | `chromadb/chroma:latest`（公共镜像） | 8000 | `docker pull` 自动拉取 |
| **nginx** | `nginx:alpine`（公共镜像） | 80 / 443 | `docker pull` 自动拉取 |

---

## 3. 服务器目录结构

```
/home/ubuntu/looma-zervi/          # $DEPLOY_PATH
├── docker/
│   ├── docker-compose.yml         # 容器编排（backend 使用 build:）
│   ├── Dockerfile.backend         # 后端镜像定义
│   ├── nginx.conf                 # Nginx 反向代理配置
│   └── certs/                     # SSL 证书（手动放置）
│       ├── api.genz.ltd.pem
│       ├── api.genz.ltd.key
│       └── ...
├── backend/
│   ├── .env                       # 环境变量（JWT / API Key 等）
│   ├── requirements.txt
│   └── src/...                    # Python 代码（CI rsync 同步）
├── docs/
└── scripts/

/var/www/
├── planetx/dist/                  # PlanetX 前端（CI rsync 同步）
└── saas/dist/                     # T-space 前端（CI rsync 同步）
```

### 挂载关系

| 容器内路径 | 宿主机路径 | 类型 | 说明 |
|-----------|-----------|------|------|
| `/app` | `../backend` | bind mount | 代码热更新（restart 即生效） |
| `/app/data` | `backend-data` | named volume | SQLite 数据库持久化 |
| `/app/chroma_data` | `chroma-data` | named volume | 向量数据持久化 |
| `/etc/nginx/nginx.conf` | `./nginx.conf` | bind (ro) | nginx 配置 |
| `/etc/nginx/certs` | `./certs` | bind (ro) | SSL 证书 |
| `/var/www/planetx/dist` | `/var/www/planetx/dist` | bind (ro) | 前端静态文件 |
| `/var/www/saas/dist` | `/var/www/saas/dist` | bind (ro) | 前端静态文件 |

---

## 4. 首次部署（手动，一次性）

### 前提

- 服务器已安装 Docker + Docker Compose
- 代码仓库已 clone 到 `$DEPLOY_PATH`
- SSL 证书已放入 `docker/certs/`
- `backend/.env` 已创建

### Step 1：同步代码到服务器

```bash
# 在本地执行
rsync -avz --delete \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='venv' \
  --exclude='data/' \
  --exclude='chroma_data/' \
  --exclude='.env' \
  --exclude='frontend/' \
  ./ \
  ubuntu@<服务器IP>:/home/ubuntu/looma-zervi/
```

### Step 2：创建 `.env` 文件

```bash
# SSH 到服务器
ssh ubuntu@<服务器IP>

# 创建环境变量文件
cat > /home/ubuntu/looma-zervi/backend/.env << 'EOF'
JWT_SECRET=<你的JWT密钥>
DEEPSEEK_API_KEY=<你的DeepSeek API Key>
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
ENV=production
DATABASE_PATH=/app/data/looma.db
EOF
```

### Step 3：构建 + 启动所有容器

```bash
cd /home/ubuntu/looma-zervi
docker compose -f docker/docker-compose.yml up -d --build
```

**耗时预估**：首次 5-10 分钟（拉 chromadb/nginx 镜像 + pip install），后续秒级。

### Step 4：健康检查

```bash
# 检查容器状态
docker compose -f docker/docker-compose.yml ps

# 健康检查
curl -s http://localhost:5000/health  # Backend
curl -s http://localhost/health        # Nginx → Backend
```

---

## 5. 日常 CI/CD 流水线（全自动）

每次 push `main` 后自动执行：

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐
│ frontend-build│    │ backend-test │    │     deploy       │
│ pnpm build   │    │ pytest 53个  │    │ rsync 代码+前端   │
│ 两个前端包    │    │ 测试用例     │    │ → restart backend │
│              │    │              │    │ → curl 健康检查   │
└──────────────┘    └──────────────┘    └──────────────────┘
       │                   │                      │
       └───────────────────┴──────────────────────┘
                     并行执行                依赖前两者成功
```

### CI 部署步骤

| Step | 操作 | 耗时 |
|------|------|------|
| Bootstrap | 确保目录 + `.env` 存在 | < 5s |
| Sync code | rsync 后端代码到服务器 | < 10s |
| Upload dist | rsync PlanetX / Saas 前端产物 | < 15s |
| Restart | `docker compose up -d && restart backend` | < 10s |
| Health check | curl `localhost:5000/health` + `localhost/health` | < 5s |

**总部署耗时**：~30 秒（不含前端 build 和后端 test）

### SSH 稳定性保障

- `ServerAliveInterval=30`：每 30 秒心跳保活
- `ServerAliveCountMax=10`：允许 10 次失败（5 分钟容错）
- rsync 也通过 `-e "$SSH_CMD"` 复用保活参数

---

## 6. 域名与路由

| 域名 | 转发 | 说明 |
|------|------|------|
| `api.genz.ltd` | → backend:5000 | 后端 API（支持 SSE 流式） |
| `planetx.genz.ltd` | → /var/www/planetx/dist | PlanetX 前端 SPA |
| `t.genz.ltd` | → /var/www/saas/dist | T-space 前端 SPA |

> 当前仅监听 80 端口（HTTP）。HTTPS 需在 `docker/certs/` 放置证书后启用。

---

## 7. 需要研判的问题

### 7.1 SSL 证书管理

- [ ] `docker/certs/` 目录目前为空，证书如何获取？
- [ ] 是否使用 Let's Encrypt + certbot？还是腾讯云 SSL 证书？
- [ ] 如果使用 certbot，需要额外容器（如 `certbot` + cron 自动续期）

### 7.2 ChromaDB 数据

- [ ] 当前使用 Docker named volume（`chroma-data`），数据在 `/var/lib/docker/volumes/`
- [ ] 是否需要改为 bind mount 以便于备份？（如 `./chroma_data:/chroma/chroma`）

### 7.3 后端代码热更新

- [ ] `restart backend` 有 2-3 秒停机窗口，是否可接受？
- [ ] 如需零停机，可改为蓝绿部署或 `docker compose up -d --force-recreate`

### 7.4 监控与告警

- [ ] 是否需要配置容器健康检查（`HEALTHCHECK` 指令）？
- [ ] 是否需要接入日志聚合（如 Docker → 腾讯云 CLS）？

### 7.5 回滚策略

- [ ] Git revert + CI 自动部署即可回滚
- [ ] 是否需要保留多版本 Docker 镜像？

### 7.6 依赖变更

- [ ] 当 `requirements.txt` 变更时，需手动 `docker compose build backend` 重建镜像
- [ ] 是否需要 CI 自动检测 `requirements.txt` 变更并触发 rebuild？

---

## 8. 相关文件

| 文件 | 路径 |
|------|------|
| 容器编排 | `docker/docker-compose.yml` |
| 后端镜像 | `docker/Dockerfile.backend` |
| Nginx 配置 | `docker/nginx.conf` |
| CI/CD 流水线 | `.github/workflows/deploy.yml` |
| 本方案文档 | `docs/Docker容器部署方案.md` |

---

> **下一步**：团队研判通过后，按第 4 节步骤执行首次手动部署，验证容器通信正常后，CI/CD 流水线即可投入使用。
