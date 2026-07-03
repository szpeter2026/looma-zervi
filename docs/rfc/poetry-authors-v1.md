# RFC: `GET /v1/poetry/authors` 诗人分页接口

> **状态：** Draft · **作者：** Jason · **Review：** szbenyx  
> **日期：** 2026-07-04  
> **依据：** DECISION_RESPONSE.md #7 · DUAL_REPO_WORK_GUIDE P1-L1

---

## 1. 背景

`szbolent-portal/src/api/poetry.ts` 的 `getPoets()` 当前通过多次 `GET /v1/poetry/browse` 客户端聚合作者，存在：

- 性能差（固定扫 5 页 × 50 条）
- 诗人 `poem_count` 不准确（仅扫描窗口内计数）
- `poetId` 为字符串 hash，刷新后可能不一致

Looma 无独立 `poets` 表；作者信息存于 `poems.author` 字段。

---

## 2. 目标

提供服务端分页聚合接口，portal 与 future 客户端只消费契约，不再客户端扫页。

---

## 3. 提议 API

### `GET /v1/poetry/authors`

**Query**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | 1 | 页码 |
| `per_page` | int | 24 | 每页条数，max 50 |
| `dynasty` | string | — | 可选朝代过滤 |
| `keyword` | string | — | 可选作者名模糊搜索 |

**Response 200**

```json
{
  "items": [
    {
      "author": "李白",
      "dynasty": "唐",
      "poem_count": 983
    }
  ],
  "total": 1159,
  "page": 1,
  "per_page": 24
}
```

**说明**

- 不引入 numeric `poet_id` v1；portal 可用 `author` 字符串作 URL slug 或继续 hash 但数据来自服务端 `poem_count`
- 可选 v1.1：`poet_slug` 拼音字段

---

## 4. 实现要点（后端）

- SQL：`SELECT author, dynasty, COUNT(*) AS poem_count FROM poems WHERE ... GROUP BY author ORDER BY poem_count DESC LIMIT/OFFSET`
- 路由：`poetry_routes.py` 新增 `@poetry_bp.route("/authors")`
- 契约：纳入 `backend/contracts/poetry.v1.json`（szbenyx 维护）

---

## 5. Portal 迁移

```typescript
// poetry.ts — 替换 getPoets 扫页逻辑
async getPoets(params) {
  const { data } = await axios.get(`${LOOMA_BASE}/v1/poetry/authors`, { params })
  // map to Poet view type
}
```

---

## 6. 验收

- [ ] `curl /v1/poetry/authors?page=1&per_page=10` 返回稳定 JSON
- [ ] portal 诗人列表不再调用 browse 扫页
- [ ] 契约文件与 OpenAPI 同步

---

## 7. 时间线

| 阶段 | 负责 | 目标 |
|------|------|------|
| RFC Review | szbenyx | W2 初 |
| 后端实现 | Jason / szbenyx | W2 中 |
| portal adapter | portal 组 | 后端合并后 |
