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

### 2.1 架构评分

| 模块 | 完成度 | 问题 |
|------|--------|------|
| 平台适配层 (Network/Storage/Auth/Device) | 100% | ✅ 无问题 |
| shared-core (ApiClient/Endpoints/Types) | 95% | endpoints.ts 已定义，但缺少类型定义 |
| 邮箱登录/注册 | 90% | ✅ 已对接后端 |
| 求职者首页 (HomePage.ets) | 85% | `loadJobs()` 已正确调用 `GET /v1/jobs` |
| 答题游戏 (GamePage.ets) | 80% | **严重依赖 mock 降级**，见下文 |
| 岗位详情 (JobDetailPage.ets) | 85% | 已正确调用 `GET /v1/jobs/:id` |
| 个人中心 (ProfilePage.ets) | 80% | 用户卡片 + 菜单 |
| 合伙人仪表盘 (PartnerDashboardPage.ets) | 75% | 对接 `/v1/job-posts` |
| 候选人列表 (CandidateListPage.ets) | 5% | **仅骨架 Text，无数据加载** |
| 职位发布表单 (JobManagePage.ets) | 5% | **仅骨架 Text，无表单** |
| 简历页 | 0% | 文件不存在 |
| AI 聊天页 | 0% | 文件不存在 |

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

### 🔴 P0 — 阻塞级（不改则功能不可用）

#### 3.1 `entry/src/main/ets/shared-core/api/endpoints.ts`

**现状**：已正确定义端点路径，无需修改。确认 `JOBS.LIST = '/v1/jobs'` 等值与后端一致即可。

#### 3.2 `entry/src/main/ets/pages/GamePage.ets`

**问题**：网络响应格式不匹配，导致始终走 mock 降级。

**需要修改**：

```typescript
// 修改 init() 方法（第78-119行）
// 旧代码:
if (response.success && response.data) {
  this.sessionId = response.data.session_id;
  // ...
}

// 新代码 (后端直接返回数据，无 {success, data} 包装):
const resp = response.data || response as unknown as GameStartResponse;
if (resp?.session_id) {
  this.sessionId = resp.session_id;
  if (resp.questions && resp.questions.length > 0) {
    this.currentQ = resp.questions[0];
    this.totalQuestions = resp.total || resp.questions.length;
    this.questionIndex = 0;
    this.startCountdown();
  } else {
    this.errorMsg = '暂无题目';
    this.pageState = 'error';
  }
}
```

**同样需要修改** `submitAnswer()` (第152行) 和 `loadResult()` (第229行)。

#### 3.3 `entry/src/main/ets/pages/HomePage.ets`

**问题**：`loadJobs()` (第89行) 中对 `response.data` 的检查与后端响应格式可能不匹配。

**需要修改**：

```typescript
// 修改 loadJobs() 第99-104行:
// 后端 GET /v1/jobs 直接返回 {jobs: [...], total: N}
const response = await this.networkAdapter.get('/v1/jobs', paramsObj);
// 兼容两种包装格式
const data = (response as any).data || response;
if (data?.jobs) {
  this.jobs = data.jobs;
}
```

#### 3.4 `entry/src/main/ets/pages/JobDetailPage.ets`

**验证**：`init()` 方法已正确调用 `GET /v1/jobs/${this.jobId}`，后端返回 `{job: {...}}`。

**修改第55-59行**：

```typescript
const resp = (response as any).data || response;
if (resp?.job) {
  this.job = resp.job;
}
```

### 🟡 P1 — 补页面（后端就绪但无前端）

#### 3.5 新建 `entry/src/main/ets/pages/ResumePage.ets`

对接以下端点：

```typescript
// 我的简历列表
GET /v1/resume/list  → { resumes: [...], total: N }

// 上传简历
POST /v1/resume/upload (multipart/form-data)

// 解析简历  
POST /v1/resume/parse → { extracted: {...} }

// AI 分析
GET /v1/resume/analysis?resume_id=xxx → { resume_id, title, extracted, analysis }

// 删除
DELETE /v1/resume/:resume_id → { message: "deleted" }

// 简历优化建议
POST /v1/resume/improve → { improvements: {...} }
```

**页面结构建议**：
- 顶部：上传按钮 (选择 PDF/DOCX 文件)
- 列表：已上传简历卡片（文件名、日期、解析状态）
- 点击进入详情 → AI 分析结果 + 优化建议
- 长按/左滑删除

#### 3.6 新建 `entry/src/main/ets/pages/AiChatPage.ets`

对接：

```typescript
POST /v1/ask → { answer: "...", sources: [...] }
POST /v1/ask/stream (SSE)
GET  /v1/ask/history
```

#### 3.7 完善 `entry/src/main/ets/pages/CandidateListPage.ets`

对接：

```typescript
GET /v1/job-posts/:id/matches  → 候选人匹配列表
```

#### 3.8 完善 `entry/src/main/ets/pages/JobManagePage.ets`

对接：

```typescript
POST   /v1/job-posts      → 创建职位
GET    /v1/job-posts       → 列表
PUT    /v1/job-posts/:id   → 更新
DELETE /v1/job-posts/:id   → 删除
```

### 🟢 P2 — 体验优化

#### 3.9 倒计时动画

**现状**：`GamePage.ets` 第122行已有 `startCountdown()` 3→2→1 逻辑，但使用 `setInterval`。

**建议**：使用 `animateTo` 增加数字缩放/淡出动画。

#### 3.10 首页快捷入口

**现状**：`HomePage.ets` `buildQuickEntry()` (第282行) 中"我的简历"和"AI 助手"没有 `onClick` 事件。

```typescript
// 修复: 简历入口
Column() {
  Text('📊').fontSize(24)
  Text('我的简历').fontSize(12).fontColor('#374151').margin({ top: 6 })
}
.alignItems(HorizontalAlign.Center)
.margin({ left: 28 })
.onClick(() => router.pushUrl({ url: 'pages/ResumePage' }))  // ← 添加

// AI 助手入口
Column() {
  Text('🤖').fontSize(24)
  Text('AI 助手').fontSize(12).fontColor('#374151').margin({ top: 6 })
}
.alignItems(HorizontalAlign.Center)
.margin({ left: 28 })
.onClick(() => router.pushUrl({ url: 'pages/AiChatPage' }))  // ← 添加
```

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
