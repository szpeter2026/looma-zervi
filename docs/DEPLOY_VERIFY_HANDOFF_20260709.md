# looma-zervi 部署验收 · Run #48

> **日期：** 2026-07-09  
> **版本：** b89781e  
> **API：** http://api.genz.ltd  
> **后端机：** 1.14.202.161  
> **门户：** http://47.115.168.107  
> **验证人：** 嘟嘟（自动化 curl 验证）

## 验证结果总览

| # | 端点 | 方法 | 状态 | 备注 |
|---|------|------|------|------|
| 1 | `/` | GET | ✅ PASS | 服务健康，返回全部端点列表 |
| 2 | `/v1/poetry/stats` | GET | ✅ PASS | 58059 首（唐 56570 + 宋 1489） |
| 3 | `/v1/poetry/browse` | GET | ✅ PASS | 分页浏览，支持 dynasty/keyword 过滤 |
| 4 | `/v1/poetry/:id` | GET | ✅ PASS | 单篇详情含全文（验证 id=1） |
| 5 | `/v1/poetry/random` | GET | ✅ PASS | 随机返回一首 |
| 6 | `/v1/poetry/search` | GET | ✅ **FIXED** | 504 已修复，<1s 返回，`search_backend=sqlite` |
| 7 | `/v1/auth/register` | POST | ✅ PASS | JWT 签发正常，tier=free |
| 8 | `/v1/auth/login` | POST | ✅ PASS | 登录返回 access_token |
| 9 | `/v1/quota` | GET | ✅ PASS | ask: 30/day, job_match: 5/day, rag: 10/day, resume_parse: 3/day |
| 10 | `/v1/payment/plans` | GET | ✅ PASS | 3 档定价，provider=wechat，region=CN |
| 11 | `/v1/compliance/consent/required` | GET | ✅ PASS | 9 个 scope 列出（ask_rag, credit_query 等） |
| 12 | `/v1/compliance/consent/grant` | POST | ✅ PASS | 授权成功，返回 consent_id |
| 13 | `/v1/compliance/consent/status` | GET | ✅ PASS | 状态正确（grant 后 ask_rag=true） |
| 14 | `/v1/ask` | POST | ⚠️ **FAIL** | **见下方详细分析** |

## ⚠️ 唯一未通过项：`POST /v1/ask` 授权检查 Bug

### 现象

按交接说明，Ask 授权走 `/v1/compliance/consent/grant`（不是 `auth/bridge`）。
完整流程验证如下：

```
1. POST /v1/auth/register → 获得 JWT                              ✅
2. GET  /v1/compliance/consent/status → ask_rag = false           ✅ (正确，未授权)
3. POST /v1/compliance/consent/grant {scope: "ask_rag"}          ✅
   → {"already_granted": false, "consent_id": "695ada30-..."}
4. GET  /v1/compliance/consent/status → ask_rag = true            ✅ (正确，已授权)
5. POST /v1/ask {query: "请赏析静夜思"}                           ❌
   → {"error": "consent_required", "required_scope": "ask_rag"}
```

### 问题定位

- **Consent grant 机制本身正常**：`/v1/compliance/consent/status` 确认授权已写入（`ask_rag: true`）
- **但 `/v1/ask` 端点的授权检查没有识别到已授权状态**
- 可能原因：
  1. ask 路由的 consent 中间件查询的表/缓存与 grant 写入的不一致
  2. consent 检查有缓存层，grant 后未刷新
  3. ask 路由检查的 scope 名称与 grant 存储的 scope 名称不匹配（大小写/前缀差异）

### 复现步骤

```bash
# 1. 注册获取 token
REG=$(curl -sf -X POST http://api.genz.ltd/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"bug-repro@genz.ltd","password":"BugRepro123!"}')
TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. 授权 ask_rag
curl -sf -X POST http://api.genz.ltd/v1/compliance/consent/grant \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope":"ask_rag"}'
# → {"already_granted": false, "consent_id": "..."}

# 3. 确认授权状态
curl -sf http://api.genz.ltd/v1/compliance/consent/status \
  -H "Authorization: Bearer $TOKEN"
# → {"status": {"ask_rag": true, ...}}  ← 授权确认写入

# 4. 调用 ask — 仍然被拦
curl -sf -X POST http://api.genz.ltd/v1/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"请赏析静夜思"}'
# → {"error": "consent_required", "required_scope": "ask_rag"}  ← BUG
```

### 建议修复方向

检查 `ask_routes.py` 中的 consent 检查逻辑：

```python
# 可能的问题代码（推测）：
# consent 检查直接查 consent 表，但条件可能不匹配
# 例如检查 scope = 'ask_rag' AND status = 'granted'
# 但实际存储的 scope 字段值可能是 'ask' 或其他变体

# 或者检查是否用了不同的查询路径：
# - grant 写入：consent 表
# - ask 检查：可能查了 user_scopes 缓存表 或 JWT payload
```

## search 504 修复确认

Run #47 中 `/v1/poetry/search` 超时 30s（ChromaDB 向量检索卡死）。
Run #48 已修复，降级到 SQLite FTS 全文搜索：

```bash
GET /v1/poetry/search?q=明月&n=3
# 响应时间 <1s
# 返回 3 条结果（帝京篇·三、咏弓、轩游宫十五夜）
# "search_backend": "sqlite"  ← 确认降级到 SQLite
```

✅ 搜索功能恢复，响应正常。

## verify-p0-local.sh 脚本兼容性说明

验证脚本中 ask 测试只验证了 **未授权时被拦截**（返回 403 consent_required），
未覆盖 **授权后放行** 的正向流程。建议补充以下用例：

```bash
# 在 verify-p0-local.sh 的 step 6 之后追加：
echo "==> 6b. Ask allowed after ask_rag consent"
curl -sf -X POST "$API_BASE/v1/compliance/consent/grant" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scope":"ask_rag"}' >/dev/null

CODE=$(curl -s -o /tmp/p0-ask-ok.json -w '%{http_code}' -X POST "$API_BASE/v1/ask" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"test question"}')
if [ "$CODE" != "200" ] && [ "$CODE" != "422" ]; then
  echo "Ask still blocked after consent: $CODE"
  cat /tmp/p0-ask-ok.json
  exit 1
fi
```

## 签字

- [ ] **后端开发**：确认 ask consent 检查 bug，修复后重新部署
- [ ] **前端对接**：search 已可用，门户语义搜索功能可接入；ask 待修复后再联调
- [ ] **部署验收**：13/14 项通过，1 项待修复（ask consent check）
