# 合伙人 Dashboard API 对照表

> **📋 修正状态：** 第 1 轮（路径修正）✅ · 第 2 轮（字段映射）✅ · 文档勘误修订 ✅（2026-07-11）  
> **联调前对照 §8 逐条勾验。**
>
> **记录日期：** 2026-07-11  
> **用途：** 前端开工前与后端对齐；合伙人按本表接入，勿假设 `/v1/enterprise/jobs` 路径。  
> **真源：** Flask 路由 + `@looma/shared-core` 的 `createApi.ts`

---

## 0. 核心勘误（必读）

| 合伙人假设 | 实际实现 | 说明 |
|-----------|---------|------|
| `ENTERPRISE.JOBS` → `/v1/enterprise/jobs` | ❌ **不存在** | 职位 CRUD 在独立路径 `/v1/job-posts` |
| `ApiClient` Enterprise 方法 = 0 | ❌ **不准确** | `createEnterpriseApi` 已有 **8 个方法** |
| Job 写操作完全没有 | ❌ **不准确** | 后端 + `createJobPostApi` 已有完整 CRUD |
| `GET /v1/enterprise/candidates/:job_id` | ❌ **不存在** | 改用 `GET /v1/job-posts/:id/matches` |
| `GET /v1/resume/analysis/:resume_id` | ❌ **不存在** | 候选人洞察走 `GET /v1/enterprise/candidate/:id` |
| `/v1/jobs/*` = HR 发布职位 | ❌ **概念混淆** | `/v1/jobs/*` 是 C 端工具（上传 JD → AI 解析 → 匹配） |

---

## 1. 合伙人需求 → 实际端点映射

| 合伙人 Dashboard 需要 | 实际端点 | 方法 | 后端 | shared-core ApiClient | 鉴权 |
|--------------------|---------|------|------|----------------------|------|
| 获取我的企业信息 | `/v1/enterprise/profile` | GET | ✅ | `createEnterpriseApi().profile()` | JWT |
| 编辑企业信息 | `/v1/enterprise/profile` | PATCH | ❌ 未实现 | — | — |
| 我发布的职位列表 | `/v1/job-posts` | GET | ✅ | `createJobPostApi().list()` | JWT + supporter+ |
| 发布新职位 | `/v1/job-posts` | POST | ✅ | `createJobPostApi().create()` | JWT + supporter+ |
| 编辑职位 | `/v1/job-posts/:id` | PUT | ✅ | `createJobPostApi().update()` | JWT + supporter+ |
| 下线/删除职位 | `/v1/job-posts/:id` | DELETE | ✅ | `createJobPostApi().remove()` | JWT + supporter+ |
| 某职位的匹配候选人 | `/v1/job-posts/:id/matches` | GET | ✅ | `createJobPostApi().matches()` | JWT + supporter+ |
| 企业全部候选人列表 | `/v1/enterprise/candidates` | GET | ✅ | `createEnterpriseApi().candidates()` | JWT + supporter+ |
| 单个候选人详情（含人格） | `/v1/enterprise/candidate/:id` | GET | ✅ | `createEnterpriseApi().getCandidate()` | JWT + supporter+ |
| 从分享码导入候选人 | `/v1/enterprise/candidates/import-share` | POST | ✅ | `createEnterpriseApi().importFromShare()` | JWT + supporter+ |
| 手动添加候选人 | `/v1/enterprise/candidates/add` | POST | ✅ | `createEnterpriseApi().addCandidate()` | JWT + supporter+ |
| 创建企业 | `/v1/enterprise/create` | POST | ✅ | `createEnterpriseApi().create()` | JWT |
| 候选人简历 AI 分析 | `/v1/resume/analysis/:id` | GET | ❌ 未实现 | — | — |
| 简历解析（上传/文本） | `/v1/resume/parse` / `/upload` | POST | ✅ | `createResumeApi().parse()` / `.upload()` | 可选 JWT + consent |
| 简历改进建议 | `/v1/resume/improve` | POST | ✅ 后端有 | ❌ ApiClient **未封装** | 可选 JWT + consent |

---

## 2. 端点详细对照（合伙人表格 ✅/❌）

| 端点 | 方法 | 后端状态 | ApiClient 状态 | 用途 |
|------|------|---------|---------------|------|
| `/v1/enterprise/profile` | GET | ✅ | ✅ `profile()` | 企业信息展示 |
| `/v1/enterprise/profile` | PATCH | ❌ | ❌ | 编辑企业信息（**待建**） |
| `/v1/enterprise/jobs` | GET | ❌ 路径不存在 | ❌ | — |
| `/v1/job-posts` | GET | ✅ | ✅ `createJobPostApi().list()` | 我发布的职位列表 |
| `/v1/job-posts` | POST | ✅ | ✅ `.create()` | 发布新职位 |
| `/v1/job-posts/:id` | PUT | ✅ | ✅ `.update()` | 编辑职位 |
| `/v1/job-posts/:id` | DELETE | ✅ | ✅ `.remove()` | 下线/删除职位 |
| `/v1/job-posts/:id/matches` | GET | ✅ | ✅ `.matches()` | 查看该职位匹配候选人 |
| `/v1/enterprise/candidates` | GET | ✅ | ✅ `.candidates()` | 企业候选人池（非按职位） |
| `/v1/enterprise/candidate/:id` | GET | ✅ | ✅ `.getCandidate()` | 候选人详情 + profile_data |
| `/v1/enterprise/candidates/:job_id` | GET | ❌ | ❌ | 用 `job-posts/:id/matches` 替代 |
| `/v1/resume/analysis/:resume_id` | GET | ❌ | ❌ | 用 candidate detail 或后续新建 |

---

## 3. 两套「Jobs」概念区分

### A. `/v1/job-posts` — HR 职位发布（合伙人 Dashboard 用这个）

- 持久化表：`job_posts`
- 按 `user_id` 归属发布者
- 完整 CRUD + matches
- 工厂函数：`createJobPostApi(client)`

### B. `/v1/jobs/*` — C 端求职工具（不是 HR 发布）

| 端点 | 方法 | 用途 |
|------|------|------|
| `/v1/jobs/list` | GET | 列出已上传/解析的 JD 文档 |
| `/v1/jobs/upload` | POST | 上传 JD 文件 |
| `/v1/jobs/parse` | POST | 解析 JD 文本 |
| `/v1/jobs/match` | POST | 简历 ↔ 职位 AI 匹配评分 |

- 工厂函数：`createJobsApi(client)` — list / upload / parse / match 均已封装

---

## 4. 响应 JSON Shape

### 4.1 `GET /v1/enterprise/profile`

```json
{
  "id": "uuid",
  "name": "测试企业",
  "domain": "example.com",
  "plan": "free",
  "created_at": "2026-07-11 12:00:00",
  "role": "admin"
}
```

错误：`404 { "error": "not_found", "message": "不属于任何企业" }`

> **注意：** 响应中的 `plan` 是**企业套餐字段**（`enterprises.plan`），不是当前登录用户的 `tier`。用户 tier 请从 `GET /v1/auth/profile` 或 `GET /v1/payment/status` 获取。

---

### 4.2 `GET /v1/job-posts`

```json
{
  "job_posts": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "title": "产品经理",
      "company": "未来科技",
      "description": "负责…",
      "requirements": ["创新", "领导力"],
      "status": "active",
      "created_at": "2026-07-11 12:00:00",
      "updated_at": "2026-07-11 12:00:00"
    }
  ],
  "limit": 3,
  "count": 1
}
```

`requirements` 存库为字符串，响应时若为 JSON 数组会自动解析。

---

### 4.3 `POST /v1/job-posts`

**请求：**
```json
{
  "title": "产品经理",
  "company": "未来科技",
  "description": "岗位描述…",
  "requirements": ["创新", "领导力"],
  "status": "active"
}
```

**响应 `201`：** 单个 `JobPost` 对象（同 4.2 数组元素）

**错误：**
- `403` free tier 或无权限
- `429` `{ "error": "quota_exceeded", "limit": 3, "current": 3, "upgrade": { "tier": "pro" } }`

---

### 4.4 `PUT /v1/job-posts/:id`

**请求：** 任意子集 `{ title, company, description, requirements, status }`  
**响应 `200`：** 更新后的 `JobPost`  
**`status` 值：** `active` | `closed` | `draft`

---

### 4.5 `DELETE /v1/job-posts/:id`

**响应 `200`：** `{ "ok": true }`

---

### 4.6 `GET /v1/job-posts/:id/matches`

```json
{
  "job_post": { "...JobPost" },
  "matches": [
    {
      "candidate": {
        "id": "uuid",
        "enterprise_id": "uuid",
        "user_id": "uuid",
        "name": "张三",
        "email": "zhang@example.com",
        "phone": null,
        "status": "new",
        "profile_data": {
          "personality_type": "探索者",
          "personality_detail": { "emoji": "🎨", "traits": ["创新"] },
          "xp": 50,
          "level": 2,
          "share_code": "ABC123"
        },
        "created_at": "2026-07-11 12:00:00"
      },
      "match_score": 0.67
    }
  ],
  "total": 1
}
```

> 匹配逻辑为 MVP 关键词重叠评分，非 LLM 深度匹配。

---

### 4.7 `GET /v1/enterprise/candidates`

```json
{
  "candidates": [ "...Candidate 同 4.6" ],
  "limit": 20,
  "total": 5
}
```

---

### 4.8 `GET /v1/enterprise/candidate/:id`

```json
{
  "id": "uuid",
  "enterprise_id": "uuid",
  "user_id": "uuid",
  "name": "张三",
  "email": "zhang@example.com",
  "phone": null,
  "status": "new",
  "profile_data": {
    "personality_type": "探索者",
    "personality_detail": { "...": "..." },
    "xp": 50,
    "level": 2,
    "share_code": "ABC123"
  },
  "created_at": "2026-07-11 12:00:00"
}
```

> **候选人「分析」目前在这里：** `profile_data` 含 PlanetX 人格测试结果。无独立 resume analysis 端点。

---

## 5. 前端接入示例

```typescript
// 可参考实现（仅 Enterprise API — 企业信息 + 候选人）：
//   looma-zervi/frontend/packages/saas/src/features/candidates/Candidates.tsx
//   looma-zervi/frontend/packages/saas/src/features/candidates/CandidateDetail.tsx
// 注意：SaaS 侧尚无 Job Posts 页面；职位 CRUD 需自行用 createJobPostApi 实现（见下方示例）。

import {
  createEnterpriseApi,
  createJobPostApi,
} from "@looma/shared-core";
import { createSaasApiClient } from "./api/saasApiClient";

const client = createSaasApiClient();
const enterprise = createEnterpriseApi(client);
const jobPosts = createJobPostApi(client);

// Dashboard 加载
const profile = await enterprise.profile();
const { job_posts } = await jobPosts.list();
const { candidates } = await enterprise.candidates();

// 职位操作
const post = await jobPosts.create({ title: "产品经理", company: "XX" });
await jobPosts.update(post.id, { status: "closed" });
const { matches } = await jobPosts.matches(post.id);

// 候选人
const candidate = await enterprise.getCandidate(matches[0].candidate.id);
```

**常量路径：** `frontend/packages/shared-core/src/constants/routes.ts`  
**类型定义：** `frontend/packages/shared-core/src/types/enterprise.ts`

---

## 6. 待后端补充（合伙人若强依赖）

| 优先级 | 端点 | 说明 |
|--------|------|------|
| P1 | `PATCH /v1/enterprise/profile` | 编辑企业名称/域名 |
| P1 | `createResumeApi().improve()` | 封装已有 `POST /v1/resume/improve` |
| P2 | `GET /v1/resume/analysis/:candidate_id` | 统一候选人简历+AI 洞察（或复用 candidate detail） |
| P2 | 职位-候选人投递关联表 | 当前 matches 为关键词评分，非真实投递流 |

---

## 7. Tier 门控提醒

以下端点需要 **supporter+** tier，free 用户返回 `403`：

- 全部 `/v1/job-posts/*`
- `/v1/enterprise/candidates`
- `/v1/enterprise/candidate/:id`
- `/v1/enterprise/candidates/import-share`
- `/v1/enterprise/candidates/add`

创建/加入企业（`create` / `join` / `profile`）仅需 JWT，不限 tier。

---

## 8. 合伙人交付勘误 — 路径修正清单

> **第 1 轮（✅ 已完成）：** 7 个端点路径从 `/v1/enterprise/*` → `/v1/job-posts/*`。  
> **第 2 轮（✅ 已完成）：** 4 项字段映射 + 路由修正全部落实。  
> **当前状态：100% 对齐后端，可联调。**

### 第 1 轮修正对照（已完成）

| # | 合伙人原始路径 | 修正后路径 | 状态 |
|---|--------------|-----------|------|
| 1 | `GET /v1/enterprise/jobs` | `GET /v1/job-posts` | ✅ 已改 |
| 2 | `POST /v1/enterprise/jobs` | `POST /v1/job-posts` | ✅ 已改 |
| 3 | `GET /v1/enterprise/jobs/:id` | `getJobPostDetail()` 已删除；从 list 过滤 | ✅ 已改 |
| 4 | `PUT /v1/enterprise/jobs/:id` | `PUT /v1/job-posts/:id` | ✅ 已改 |
| 5 | `DELETE /v1/enterprise/jobs/:id` | `DELETE /v1/job-posts/:id` | ✅ 已改 |
| 6 | `GET /v1/enterprise/candidates/:job_id` | `GET /v1/job-posts/:id/matches` | ✅ 已改 |
| 7 | `PATCH /v1/enterprise/profile` | 后端未实现；用户 tier 从 auth/status 获取 | ✅ 已处理 |

### 第 2 轮修正（✅ 已完成 — 字段映射 + 路由确认）

| # | 问题 | 修正前 | 修正后 | 状态 |
|---|------|-------|-------|------|
| A | `GET /v1/job-posts/:id` 不存在 | `ApiClient.ets` 有 `getJobPostDetail()` | ❌ 已删除方法；从 list 结果 `find(p => p.id === id)` 取单条 | ✅ |
| B | 列表外层 key | `response.data['items']` | `response.data['job_posts']` | ✅ |
| C | PartnerJob 字段 | 含 `applicant_count` / `location` | 改为 `company` / `description` / `requirements` / `user_id` / `updated_at` | ✅ |
| D | 候选人计数 | `calcTotalCandidates()` 假设字段 | 改为 `0 + TODO` 注释（数量在 `/matches.total`）；UI 替换为 👥 查看候选人按钮 | ✅ |

### 后端路由完整清单（真源）

```
GET    /v1/job-posts              →  { job_posts: [...], limit: N, count: N }
POST   /v1/job-posts              →  单个 job_post 对象 (201)
PUT    /v1/job-posts/:id          →  更新后的 job_post 对象
DELETE /v1/job-posts/:id          →  { ok: true }
GET    /v1/job-posts/:id/matches  →  { job_post: {...}, matches: [...], total: N }
```

> **注意：没有 `GET /v1/job-posts/:id` 单条端点。**

### 响应结构对照

合伙人按 `/v1/enterprise/jobs` 假设的返回格式**必须对齐** §4 节的实际 JSON Shape：

| 场景 | 实际响应 key | 说明 |
|------|-------------|------|
| 职位列表 | `{ "job_posts": [...], "limit": 3, "count": N }` | 外层 key 是 `job_posts`，不是 `jobs` 或 `items` |
| 单个职位 | `{ "id", "title", "company", "description", "requirements", "status", ... }` | `requirements` 存库字符串，响应自动反序列化 |
| 匹配候选人 | `{ "job_post": {...}, "matches": [{ "candidate": {...}, "match_score": 0.67 }], "total": N }` | 候选人嵌套在 `matches[].candidate` 里；计数取 `total` |
| 候选人详情 | `{ "id", "name", "email", "profile_data": { "personality_type", ... } }` | 人格数据在 `profile_data` 对象中 |

### 合伙人 Dashboard 页面引用修正

```
PartnerDashboardPage.ets   →  职位列表: response.job_posts
                              职位匹配计数: 调 GET /job-posts/:id/matches 取 response.total
                              企业名称/域名: GET /v1/enterprise/profile（name, domain, role）
                              用户 tier: GET /v1/auth/profile 或 /v1/payment/status（勿用 profile.plan 当用户 tier）

JobManagePage.ets          →  POST/PUT 请求体用 §4.3-4.4 的字段名
                              单条无 GET 端点，编辑时从 list() 缓存 find(p => p.id === id) 填充表单

CandidateListPage.ets      →  response.matches.forEach(m => m.candidate)
                              response.total（该职位匹配候选人总数）
```

---

## 9. 变更日志

| 日期 | 变更 |
|------|------|
| 2026-07-11 | 初版：纠正 `/v1/enterprise/jobs` 路径误解；补齐 job-posts CRUD + JSON shape |
| 2026-07-11 | §5 补充 SaaS 参考实现文件路径（Candidates.tsx / CandidateDetail.tsx） |
| 2026-07-11 | §8 新增第 1 轮勘误：7 个端点路径 + JSON 响应结构修正清单 |
| 2026-07-11 | **§8 新增第 2 轮：** 合伙人已修正路径但仍有 4 项遗漏 — 单条端点不存在 / `job_posts` key / 候选人计数 / matches 嵌套路径 |
| 2026-07-11 | **§8 第 2 轮完成：** 合伙人 4 项字段映射 + 路由修正全部落实，当前 100% 对齐后端，可联调 |
