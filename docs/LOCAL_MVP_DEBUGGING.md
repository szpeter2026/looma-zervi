# Looma-Zervi 本地MVP联调内测指南

本文档介绍如何在本地启动完整的MVP联调内测环境，包括后端、前端Web服务和小程序开发环境。

## 📋 系统要求

### 必需软件
- **Node.js 18+** (建议使用 LTS 版本)
- **pnpm 8+** (包管理器)
- **Python 3.10+** (markitdown 依赖要求)
- **Docker Desktop** (可选，用于 ChromaDB 容器)

### 推荐环境
- macOS / Linux / WSL2 (Windows)
- 内存: 8GB+ (推荐 16GB)
- 磁盘空间: 2GB+

## 🚀 快速启动

### 一键启动完整环境

```bash
# 在项目根目录执行
./scripts/start-full-mvp.sh
```

这个脚本会自动：
1. ✅ 检查环境依赖 (Node.js, Python, pnpm, Docker)
2. ✅ 设置后端Python虚拟环境
3. ✅ 启动Flask后端 (:5200)
4. ✅ 启动PlanetX前端 (:5173)
5. ✅ 启动T-space前端 (:5174) 
6. ✅ 配置小程序开发环境
7. ✅ 启动ChromaDB向量数据库 (:8000)

### 手动分步启动

如果遇到问题，可以手动分步启动：

```bash
# 1. 启动后端
cd backend
./dev.sh  # 或: python run.py

# 2. 启动前端Web服务 (新终端)
cd frontend
pnpm install
pnpm --filter @looma/planetx dev  # PlanetX (:5173)
pnpm --filter @looma/saas dev     # T-space (:5174)

# 3. 小程序配置
cd frontend/packages/miniprogram
# 确保 config.ts 指向本地后端: http://127.0.0.1:5200
# 微信开发者工具导入此目录，设置"不校验合法域名"
```

## 🌐 服务访问地址

| 服务 | 地址 | 用途 |
|------|------|------|
| **后端API** | `http://localhost:5200` | RESTful API 接口 |
| **PlanetX (C端)** | `http://localhost:5173` | 求职者端Web应用 |
| **T-space (B端)** | `http://localhost:5174` | HR企业端Web应用 |
| **ChromaDB** | `http://localhost:8000` | 向量数据库 (可选) |
| **健康检查** | `http://localhost:5200/health` | 后端服务状态 |

## 📱 小程序本地联调

### 准备工作
1. **安装微信开发者工具**
   - 下载地址: https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html

2. **配置小程序**
   ```bash
   cd frontend/packages/miniprogram
   
   # 检查配置
   cat utils/config.ts | grep API_BASE
   # 应该显示: export const API_BASE = 'http://127.0.0.1:5200'
   
   # 如果需要修改
   sed -i '' "s|export const API_BASE = .*|export const API_BASE = 'http://127.0.0.1:5200' // dev 环境|g" utils/config.ts
   ```

3. **构建npm包**
   ```bash
   # 构建共享包
   pnpm run build:npm
   ```

### 微信开发者工具设置
1. **导入项目**: 选择 `frontend/packages/miniprogram` 目录
2. **项目设置** → **本地设置**:
   - ✅ 不校验合法域名、web-view域名、TLS版本
   - ✅ 开启调试模式
3. **工具** → **构建npm**
4. **编译**: 点击编译按钮

### 核心测试链路
按照以下顺序测试MVP核心功能：

1. **登录流程** (`app.ts` / `pages/splash`)
   - 测试微信登录 (`wechatLogin`)
   - 验证JWT令牌获取

2. **主页面** (`pages/hub/index`)
   - 加载用户个人信息
   - 显示游戏进度和任务

3. **提问功能** (`pages/ask/index`)
   - 测试RAG问答
   - 验证 `ask_rag` consent 流程

4. **结果分享** (`pages/result/index`)
   - 测试分享功能
   - 验证 `profile_share` consent 流程

## 🔧 环境配置

### 后端环境变量
复制并修改 `backend/.env.example` 到 `backend/.env`:

```bash
# Flask
FLASK_ENV=development
FLASK_PORT=5200

# 数据库
DATABASE_PATH=./data/looma.db

# 诗词向量库
POETRY_CHROMA_PATH=/Users/jason/Projects/looma-zervi/data/poetry_full

# JWT密钥
JWT_SECRET=dev-secret-change-in-production

# 微信小程序 (开发模式跳过验证)
WECHAT_APPID=your_wechat_appid
WECHAT_SECRET=your_wechat_secret
WECHAT_DEV_MODE=true

# DeepSeek API (可选)
DEEPSEEK_API_KEY=your_deepseek_api_key

# CORS配置
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

### 重要配置说明
1. **WECHAT_DEV_MODE=true**: 开发模式跳过微信登录验证
2. **POETRY_CHROMA_PATH**: 指向诗词向量库路径
3. **CORS_ORIGINS**: 允许的前端域名

## 🧪 测试验证

### API合规测试
```bash
# P0级别合规测试
bash scripts/verify-p0-local.sh

# 完整本地彩排
bash scripts/rehearsal-local.sh
```

### 小程序专用测试
```bash
# 小程序本地联调脚本
bash scripts/start-miniprogram-local.sh
```

### Web端E2E测试
```bash
cd frontend
pnpm e2e:live  # 实时环境测试
```

## 🔍 调试与监控

### 日志文件
- **后端日志**: `/tmp/looma-backend.log`
- **PlanetX日志**: `/tmp/planetx.log`
- **T-space日志**: `/tmp/saas.log`
- **ChromaDB日志**: `/tmp/chromadb.log`

### 实时查看日志
```bash
# 后端日志
tail -f /tmp/looma-backend.log

# PlanetX日志
tail -f /tmp/planetx.log

# 所有日志
tail -f /tmp/looma-backend.log /tmp/planetx.log /tmp/saas.log
```

### 服务状态检查
```bash
# 检查所有服务状态
## 🔧 核心配置说明

### API端点配置

#### 1. PlanetX (C端) - `http://localhost:5173`
PlanetX默认使用环境变量决定API后端地址：
```bash
# 启动脚本已设置正确的环境变量
export VITE_API_BASE_URL=http://127.0.0.1:5200
export VITE_API_BASE=http://127.0.0.1:5200
export VITE_SAAS_URL=http://localhost:5174
```

**重要**: 如果不设置这些环境变量，PlanetX会默认连接到远程服务器 `http://1.14.202.161`。

#### 2. T-space (B端) - `http://localhost:5174`
T-space通过Vite代理连接到本地后端：
```javascript
// frontend/vite.config.ts
server: {
  proxy: {
    '/v1': 'http://localhost:5200',
  }
}
```

#### 3. 小程序 - 微信开发者工具
小程序配置位于 `frontend/packages/miniprogram/utils/config.ts`：
```typescript
export const API_BASE = 'http://127.0.0.1:5200'
```

#### 4. 验证API连接
```bash
# 测试PlanetX API配置
./scripts/test-planetx-api.sh

# 检查后端是否运行
curl http://127.0.0.1:5200/health

# 检查PlanetX页面
curl -s http://localhost:5173 2>/dev/null && echo "✅ PlanetX运行正常"
```

### 数据库配置

#### 1. 诗词向量库 (RAG)
后端默认使用本地诗词向量库：
```bash
POETRY_CHROMA_PATH=/Users/jason/Projects/looma-zervi/data/poetry_full
```

如果向量库不存在，RAG功能会自动降级到文本匹配，不影响其他功能。

#### 2. 通用向量库 (ChromaDB)
```bash
# 本地文件模式 (默认)
CHROMA_PERSIST_DIR=./data/chroma

# 或使用Docker容器
docker run -d --name looma-chromadb -p 8000:8000 chromadb/chroma
```

#### 3. 主数据库 (SQLite)
```bash
DATABASE_PATH=./data/looma.db
```

## 🐛 常见问题

### 1. PlanetX连接到远程服务器而非本地后端
**现象**: PlanetX发送API请求到 `http://1.14.202.161` 而不是 `http://127.0.0.1:5200`

**原因**: 环境变量 `VITE_API_BASE` 未设置

**解决方案**:
```bash
# 方法1: 使用启动脚本（推荐）
./scripts/start-full-mvp.sh
# 或
./scripts/start-demo.sh

# 方法2: 手动设置环境变量
cd frontend
export VITE_API_BASE=http://127.0.0.1:5200
export VITE_API_BASE_URL=http://127.0.0.1:5200
pnpm --filter @looma/planetx dev

# 方法3: 验证环境变量
./scripts/test-planetx-api.sh
```

**验证**: 在浏览器控制台运行：
```javascript
console.log('API Base:', import.meta.env.VITE_API_BASE)
// 应该显示: http://127.0.0.1:5200
```

### 2. 端口冲突
如果端口被占用，可以修改配置：

```bash
# 修改后端端口 (backend/.env)
FLASK_PORT=5201

# 修改前端端口 (frontend/package.json scripts)
# PlanetX: "dev": "vite --port 5175"
# T-space: "dev": "vite --port 5176"
```

### 3. 依赖安装失败
```bash
# 清理并重新安装
cd backend
rm -rf venv
./dev.sh

cd frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### 4. 小程序构建问题
```bash
# 清理构建缓存
cd frontend/packages/miniprogram
rm -rf miniprogram_npm node_modules
pnpm install
pnpm run build:npm

# 微信开发者工具: 工具 → 清除缓存 → 重新构建npm
```

### 5. ChromaDB启动失败
如果Docker不可用，后端会自动降级到本地文件模式：
- 向量搜索功能受限
- 诗词RAG可能不可用
- 其他功能正常

## 📊 MVP内测清单

### 必须验证的功能
- [ ] 用户注册/登录 (Web + 小程序)
- [ ] 人格类型测试流程
- [ ] 诗词RAG问答 (`/v1/ask`)
- [ ] 企业信用查询 (`/v1/credit/check-company`)
- [ ] Consent授权流程
- [ ] 简历解析 (`/v1/resume/parse`)
- [ ] 岗位匹配 (`/v1/jobs/match`)
- [ ] 分享功能

### 平台兼容性
- [ ] Chrome/Safari/Firefox
- [ ] 微信开发者工具
- [ ] 移动端浏览器

### 性能要求
- [ ] 页面加载 < 3秒
- [ ] API响应 < 1秒
- [ ] 内存使用 < 500MB
- [ ] 并发用户数 ≥ 10

## 🚨 紧急问题处理

### 后端崩溃
```bash
# 查看崩溃原因
cat /tmp/looma-backend.log

# 重新启动
pkill -f "python run.py"
cd backend && ./dev.sh
```

### 前端无法访问
```bash
# 检查端口占用
lsof -i :5173
lsof -i :5174

# 重启前端
pkill -f "vite"
cd frontend
pnpm --filter @looma/planetx dev &
pnpm --filter @looma/saas dev &
```

### 数据库问题
```bash
# 重置开发数据库
cd backend
rm -f data/looma.db
python run.py
```

## 📈 下一步优化

### 短期目标 (P0)
- [ ] 完善错误处理日志
- [ ] 添加API文档 (Swagger)
- [ ] 配置CI/CD流水线

### 中期目标 (P1)
- [ ] 集成真实微信登录
- [ ] 部署ChromaDB到云服务
- [ ] 添加监控和告警

### 长期目标 (P2)
- [ ] 性能优化和缓存
- [ ] 多语言支持
- [ ] 高级分析功能

## 📞 技术支持

### 项目负责人
- **Jason**: PlanetX前端 + 小程序 + 后端API
- **szbenyx**: T-space前端 + 企业端功能

### 问题反馈
1. 查看相关日志文件
2. 运行验证脚本
3. 提交GitHub Issue
4. 联系项目负责人

---

**最后更新**: $(date +%Y-%m-%d)
**版本**: MVP v1.0