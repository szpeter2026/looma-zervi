# HarmonyOS 前端重构对齐文档

> 版本: v1.0 | 日期: 2026-07-11 | 后端: looma-zervi (Flask, port 5200)

---

## 1. 后台变更摘要

后端 `looma-zervi` 已完成 `/v1/jobs`、`/v1/game`、`/v1/resume` 三个 Blueprint 的 HarmonyOS 对齐端点适配。**新增 12 个端点**，全部验证通过 (HTTP 200/201/404)。

### 1.1 端点清单

| # | 方法 | 路径 | 功能 | 状态 |
|---|------|------|------|------|
| 1 | `GET` | `/v1/jobs` | 岗位列表（含分页 `?page=1&size=20`） | ✅ |
| 2 | `GET` | `/v1/jobs/search?q=关键词` | 关键词搜索岗位 | ✅ |
| 3 | `GET` | `/v1/jobs/:job_id` | 岗位详情 | ✅ |
| 4 | `GET` | `/v1/jobs/recommend` | AI 推荐岗位（需登录） | ✅ |
| 5 | `POST` | `/v1/game/start` | 开始答题游戏 | ✅ |
| 6 | `POST` | `/v1/game/answer` | 提交答案 | ✅ |
| 7 | `GET` | `/v1/game/result?session_id=xxx` | 获取答题结果 | ✅ |
| 8 | `GET` | `/v1/game/history` | 答题历史（需登录） | ✅ |
| 9 | `GET` | `/v1/resume/list` | 我的简历列表（需登录） | ✅ |
| 10 | `GET` | `/v1/resume/analysis?resume_id=xxx` | 简历 AI 分析（需登录） | ✅ |
| 11 | `DELETE` | `/v1/resume/:resume_id` | 删除简历（需登录） | ✅ |
| - | `POST` | `/v1/resume/upload` | 上传简历文件（已有） | ✅ |
| - | `POST` | `/v1/resume/parse` | 解析简历文本（已有） | ✅ |

### 1.2 后端连接信息

```
Base URL: http://10.0.2.2:5200  (HarmonyOS 模拟器)
         http://localhost:5200   (本地调试)

Auth:    Bearer Token (JWT)
         登录: POST /v1/auth/login
         Beta 测试账号: beta_free@looma.test / looma123
```

---

## 2. 前端当前状态诊断

基于 `/Users/jason/DevEcoStudioProjects/MyApplication` 的代码审查：

> **最近更新**: 2026-07-12 — P0/P1 已全部完成，P2 已完成。

### 2.1 架构评分

| 模块 | 完成度 | 问题 |
|------|--------|------|
| 平台适配层 (Network/Storage/Auth/Device) | 100% | ✅ 无问题 |
| shared-core (ApiClient/Endpoints/Types) | 100% | ✅ API 路由 + 类型已完整对齐 |
| 邮箱登录/注册 | 90% | ✅ 已对接后端 |
| 求职者首页 (HomePage.ets) | 90% | ✅ `loadJobs()` + 快捷入口已补 onClick |
| 答题游戏 (GamePage.ets) | 95% | ✅ 已重构为本地题库 + profileSync |
| 岗位详情 (JobDetailPage.ets) | 90% | ✅ 正确调用 `GET /v1/jobs/:id` |
| 个人中心 (ProfilePage.ets) | 80% | 用户卡片 + 菜单 |
| 合伙人仪表盘 (PartnerDashboardPage.ets) | 75% | 对接 `/v1/job-posts` |
| 候选人列表 (CandidateListPage.ets) | 90% | ✅ 已对接 `GET /v1/job-posts/:id/matches` |
| 职位发布表单 (JobManagePage.ets) | 90% | ✅ 已实现完整 CRUD 表单 |
| 简历页 (ResumePage.ets) | 90% | ✅ 新建，对接 `GET /v1/resume/list` + DELETE |
| AI 聊天页 (AiChatPage.ets) | 85% | ✅ 新建，对接 `POST /v1/ask` |

### 2.2 核心问题：GamePage 100% 依赖 mock 降级

`GamePage.ets` 当前行为：

```typescript
// 第84行：调用后端
const response = await this.networkAdapter.post('/v1/game/start');
if (response.success && response.data) {
  // 使用后端数据
} else {
  // 完全跳过，进入 catch
}

// 第101行：catch 全部走 mock 降级
} catch (_e) {
  this.sessionId = 'mock-session-001';
  this.currentQ = { id: 'q1', text: 'HarmonyOS 的 UI 框架叫什么？', ... };
  this.totalQuestions = 5;
}
```

**根因**：后端 `/v1/game/start` 之前返回 404，网络适配器把 404 当成网络错误抛出异常，`catch` 捕获后走 mock。现在后端已修复返回 201，但前端网络适配器对 `response.success` 的判断逻辑可能与后端返回格式不匹配。

**需要排查**：
1. `NetworkAdapter` 如何判断 `response.success`？如果后端返回 `{session_id:..., questions:[...], total:5}` 而非 `{success: true, data: {...}}`，`response.success` 会是 `false`
2. 网络适配器是否把非 2xx 响应转换成异常？404 → exception

---

## 3. 需要修改的文件清单

### 🟢 2026-07-12 更新：P0/P1/P2 已全部完成

> 详见下方各节。**所有阻塞级和补页面任务已完成**，当前可进行端到端联调。

### 🔴 P0 — 阻塞级（✅ 已完成）

#### 3.1 `entry/src/main/ets/shared-core/api/endpoints.ts`
**状态**: ✅ 已对齐，无需修改。

#### 3.2 `entry/src/main/ets/pages/GamePage.ets`
**状态**: ✅ 已完成。GamePage 已重构为本地题库 + `GameApi.profileSync()` 同步后端，不再依赖 `/v1/game/start` 网络调用。

#### 3.3 `entry/src/main/ets/pages/HomePage.ets`
**状态**: ✅ 已完成。`HarmonyNetworkAdapter.handleResponse` 将 2xx 响应体直接作为 `response.data`，`response.data.jobs` 正确访问。快捷入口已补 onClick 路由。

#### 3.4 `entry/src/main/ets/pages/JobDetailPage.ets`
**状态**: ✅ 已完成。同上，`response.data.job` 正确访问。NetworkAdapter 已自动处理后端直返格式。

### 🟡 P1 — 补页面（✅ 已完成）

#### 3.5 新建 `entry/src/main/ets/pages/ResumePage.ets`
**状态**: ✅ 2026-07-12 新建完成，180+ 行。
- `GET /v1/resume/list` → 简历列表含提取信息预览、技能标签
- `DELETE /v1/resume/:id` → 删除简历
- 登出态检查 + 空状态引导 + LoadingState

#### 3.6 新建 `entry/src/main/ets/pages/AiChatPage.ets`
**状态**: ✅ 2026-07-12 新建完成，200+ 行。
- `POST /v1/ask` → AI 对话功能，含意图标签 + 引用来源
- 聊天 UI 含用户/AI 气泡、输入框、发送按钮
- 配额检查提示

#### 3.7 完善 `entry/src/main/ets/pages/CandidateListPage.ets`
**状态**: ✅ 2026-07-12 从骨架页升级完成，130+ 行。
- `GET /v1/job-posts/:id/matches` → 候选人匹配列表含匹配分数和人格标签

#### 3.8 完善 `entry/src/main/ets/pages/JobManagePage.ets`
**状态**: ✅ 2026-07-12 从骨架页升级完成，300+ 行。
- `POST /v1/job-posts` → 创建职位表单
- `GET /v1/job-posts` → 职位列表
- `PUT /v1/job-posts/:id` → 编辑职位
- `DELETE /v1/job-posts/:id` → 删除职位
- 含跳转候选人管理入口

### 🟢 P2 — 体验优化（✅ 已完成）

#### 3.9 倒计时动画
**状态**: ✅ 已完成。GamePage 已使用 `setTimeout(400ms)` 做答题过渡动画。animateTo 增强作为后续迭代。

#### 3.10 首页快捷入口
**状态**: ✅ 2026-07-12 已完成。
- "我的简历" → `router.pushUrl({ url: 'pages/ResumePage' })`
- "AI 助手" → `router.pushUrl({ url: 'pages/AiChatPage' })`

---

## 4. 网络适配器对齐规范

### 4.1 后端响应格式规范

**列表类端点**直接返回数据，**不**用 `{success, data}` 包装：

```json
// GET /v1/jobs → 200
{ "jobs": [...], "total": 5 }

// GET /v1/jobs/:id → 200
{ "job": {...} }

// GET /v1/resume/list → 200
{ "resumes": [...], "total": 0 }
```

**操作类端点**直接返回结果：

```json
// POST /v1/game/start → 201
{ "session_id": "xxx", "questions": [...], "total": 5 }

// POST /v1/game/answer → 200
{ "correct": true, "score": 10, "explanation": "...", "completed": false }

// DELETE /v1/resume/:id → 200
{ "message": "deleted", "resume_id": "xxx" }
```

**错误响应**：

```json
// 404
{ "error": "not_found", "message": "简历不存在" }

// 400
{ "error": "bad_request", "message": "session_id required" }
```

### 4.2 前端 NetworkAdapter 兼容性

> ⚠️ **关键**：如果 `NetworkAdapter` 期望后端统一返回 `{success: bool, data: T}` 格式，则**前端需要修改**以兼容后端直接返回数据的方式。

**推荐方案**：在 NetworkAdapter 层做统一适配：

```typescript
// 在 ApiClient 或 NetworkAdapter 中增加 normalizeResponse()
function normalizeResponse<T>(response: any): T | null {
  // 后端直接返回的数据（无 success/data 包装）
  if (response && !('success' in response)) {
    return response as T;
  }
  // 有包装的格式
  if (response?.success && response?.data) {
    return response.data as T;
  }
  return null;
}
```

### 4.3 HTTP 方法规范

| 端点类型 | HTTP 方法 |
|----------|-----------|
| 列表/查询 | `GET` |
| 创建/开始 | `POST` |
| 更新 | `PUT` |
| 删除 | `DELETE` |

`GamePage.ets` 中 `loadResult()` 使用了 `GET` 方法带 query param（`?session_id=xxx`），这是正确的。

---

## 5. 端到端联调清单

### 5.1 准备工作

```bash
# 1. 启动后端
cd /Users/jason/Projects/looma-zervi/backend
source venv/bin/activate
python run.py
# → http://localhost:5200

# 2. 验证健康检查
curl http://localhost:5200/health
# → {"status":"ok","service":"looma-backend"}

# 3. 获取测试 Token
curl -s -X POST http://localhost:5200/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"beta_free@looma.test","password":"looma123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
```

### 5.2 联调检查项

| # | 场景 | 测试步骤 | 预期结果 |
|---|------|---------|---------|
| 1 | 首页岗位加载 | 打开 App → 首页 | 显示 5 个 mock 岗位 |
| 2 | 岗位搜索 | 搜索"前端" | 显示 1 个岗位"前端开发工程师" |
| 3 | 岗位详情 | 点击"前端开发工程师" | 跳转 JobDetailPage，显示公司、薪资、标签 |
| 4 | 推荐岗位 | 登录后下拉刷新 | 显示带匹配分数的推荐岗位 |
| 5 | 答题游戏 | 点击"技能测评" | 3-2-1 倒计时 → 答题界面 |
| 6 | 提交答案 | 选择"ArkUI"并提交 | 显示"回答正确！"反馈 |
| 7 | 答题完成 | 答完 5 题 | 显示结果页（分数 + 性格标签 + insights） |
| 8 | 答题历史 | 进入历史页 | 显示至少 1 条已完成记录 |
| 9 | 简历列表 | 进入"我的简历" | 显示 0 条或已有简历 |
| 10 | 上传简历 | 上传 PDF 文件 | 显示解析结果 |
| 11 | 简历分析 | 点击已上传简历 | 显示 AI 分析 |
| 12 | 删除简历 | 左滑 → 删除 | 简历从列表移除 |

---

## 6. 数据结构类型定义

### 6.1 TypeScript 类型定义（建议添加到 `shared-core/types/`）

```typescript
// ---- Jobs ----
interface JobItem {
  id: string;
  title: string;
  company: string;
  location: string;
  salary_range?: string;
  salary?: string;
  description?: string;
  requirements?: string[];
  tags?: string[];
  match_score?: number;
  posted_at?: string;
  company_logo?: string;
  source?: string;
}

interface JobListResponse {
  jobs: JobItem[];
  total: number;
}

interface JobDetailResponse {
  job: JobItem;
}

// ---- Game ----
interface QuizQuestion {
  id: string;
  text: string;
  type: 'single' | 'multiple' | 'scale';
  options?: QuizOption[];
  order: number;
}

interface QuizOption {
  id: string;
  text: string;
  value: number;
}

interface GameStartResponse {
  session_id: string;
  questions: QuizQuestion[];
  total: number;
}

interface GameAnswerRequest {
  session_id: string;
  question_id: string;
  option_ids: string[];
}

interface GameAnswerResponse {
  correct: boolean;
  score: number;
  explanation?: string;
  next_question?: QuizQuestion;
  completed: boolean;
}

interface GameResultResponse {
  session_id: string;
  total_score: number;
  total_questions: number;
  correct_count: number;
  result_type?: string;
  insights?: string[];
}

interface GameHistoryItem {
  id: string;
  total_score: number;
  total_questions: number;
  correct_count: number;
  result_type: string;
  status: string;
  created_at: string;
  completed_at: string | null;
}

interface GameHistoryResponse {
  sessions: GameHistoryItem[];
  total: number;
}

// ---- Resume ----
interface ResumeItem {
  id: string;
  title: string;
  filename: string;
  file_size: number;
  uploaded_at: string;
  extracted?: Record<string, any>;
}

interface ResumeListResponse {
  resumes: ResumeItem[];
  total: number;
}

interface ResumeAnalysis {
  overall_score?: number;
  strengths?: string[];
  weaknesses?: string[];
  suggestions?: string[];
  matched_roles?: string[];
  summary?: string;
}

interface ResumeAnalysisResponse {
  resume_id: string;
  title: string;
  extracted?: Record<string, any>;
  analysis?: ResumeAnalysis | null;
}

// ---- Resume Improve ----
interface ResumeImprovement {
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  suggestions: Array<{
    area: string;
    issue: string;
    advice: string;
    example: string;
  }>;
  summary: string;
}
```

---

## 7. 浏览器调试

HarmonyOS 元服务开发时，前端 `http://10.0.2.2:5200` 需要通过模拟器直连。在调试时不方便直接使用 curl 验证时，可以通过 PC 浏览器访问：

```
http://localhost:5200/    → 完整 API 文档页 (JSON)
http://localhost:5200/v1/jobs        → 岗位列表
http://localhost:5200/v1/jobs/search?q=前端 → 岗位搜索
```

---

## 8. 附录：后端变更记录

### 文件变更

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `backend/src/db/manager.py` | 新增 | `quiz_sessions` 表 + 7个 CRUD 方法 |
| `backend/src/api/routes/game_routes.py` | 新增 | 4个 quiz 端点 (start/answer/result/history) |
| `backend/src/api/routes/jobs_routes.py` | 新增 | 4个端点 (/, /search, /:id, /recommend) |
| `backend/src/api/routes/resume_routes.py` | 新增 | 3个端点 (list, analysis, delete) |
| `backend/src/app.py` | 更新 | api_info() 端点清单 |

### 数据库变更

```sql
-- 新增表 quiz_sessions (HarmonyOS 答题游戏)
CREATE TABLE IF NOT EXISTS quiz_sessions (
    id, user_id, questions_json, current_index, answers_json,
    total_score, total_questions, correct_count, status,
    result_type, insights_json, created_at, completed_at
);
```
