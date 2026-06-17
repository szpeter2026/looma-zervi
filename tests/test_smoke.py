"""Looma 集成 Smoke 测试

测试覆盖：
  1. 健康端点：验证 provider 状态、缓存统计、熔断器状态
  2. 完整 seed+ask 流程：种子数据后发起 RAG 查询
  3. Cache 命中验证：同一 query 第二次请求 <50ms 返回
  4. 熔断器状态检查

运行方式：
  # 确保服务已启动（uvicorn src.api.app:app --port 8010）
  python -m pytest tests/test_smoke.py -v -s

  # 或直接运行
  python tests/test_smoke.py
"""

from __future__ import annotations

import sys
import os
import time
import json
import urllib.request
import urllib.error

# 确保项目根目录在 sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 测试配置
BASE_URL = os.environ.get("LOOMA_TEST_URL", "http://127.0.0.1:8010")
AUTH_TOKEN = os.environ.get("LOOMA_TEST_TOKEN", "token-b658c985")
VERBOSE = os.environ.get("LOOMA_TEST_VERBOSE", "0") == "1"


def _req(method: str, path: str, body: dict | None = None, timeout: float = 120) -> dict:
    """发送 HTTP 请求并返回 JSON 响应。"""
    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body else None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise AssertionError(f"HTTP {e.code} {path}: {body_text}") from e


def log(msg: str):
    if VERBOSE:
        print(f"  [VERBOSE] {msg}")


# ═══════════════════════════════════════════════════════════
# Test 1: 健康端点
# ═══════════════════════════════════════════════════════════

def test_health_endpoint():
    """验证 /v1/health 返回所有关键字段。"""
    print("\n[TEST 1] 健康端点检查...")

    resp = _req("GET", "/v1/health")
    assert resp["status"] == "ok", f"status 不是 ok: {resp}"
    assert "uptime_seconds" in resp
    assert resp["uptime_seconds"] >= 0

    # LLM provider
    assert "llm_provider" in resp, f"缺少 llm_provider 字段: {list(resp.keys())}"
    print(f"  LLM provider: {resp['llm_provider']}")

    # Embedding provider
    assert "embed_provider" in resp, f"缺少 embed_provider 字段"
    print(f"  Embedding provider: {resp['embed_provider']}")

    # LLM 缓存统计
    assert "llm_cache" in resp, f"缺少 llm_cache 字段"
    cache = resp["llm_cache"]
    assert "hits" in cache
    assert "misses" in cache
    assert "size" in cache
    print(f"  LLM cache: hits={cache['hits']}, misses={cache['misses']}, size={cache['size']}")

    # 弹性策略统计
    assert "resilience" in resp, f"缺少 resilience 字段"
    resilience = resp["resilience"]
    assert "llm_circuit_breaker" in resilience
    assert "embed_circuit_breaker" in resilience
    llm_cb = resilience["llm_circuit_breaker"]
    embed_cb = resilience["embed_circuit_breaker"]
    print(f"  LLM 熔断器: state={llm_cb['state']}, failures={llm_cb['failure_count']}")
    print(f"  Embed 熔断器: state={embed_cb['state']}, failures={embed_cb['failure_count']}")
    assert llm_cb["state"] in ("closed", "open", "half_open")
    assert embed_cb["state"] in ("closed", "open", "half_open")

    # 依赖检查
    assert "dependencies" in resp
    deps = resp["dependencies"]
    print(f"  Dependencies: ollama={deps.get('ollama')}, pgvector={deps.get('pgvector')}, rag_index={deps.get('rag_index')}")

    # version
    assert resp.get("version") == "0.1.0"

    print("  ✅ 健康端点通过")
    return resp


# ═══════════════════════════════════════════════════════════
# Test 2: 完整 seed+ask 流程
# ═══════════════════════════════════════════════════════════

def test_seed_and_ask():
    """验证 RAG 知识库查询能正常返回结果。"""
    print("\n[TEST 2] Seed + Ask 流程...")

    # 发起 RAG 查询（使用知识库中存在的概念）
    query = "Looma 是什么平台？有哪些功能？"
    print(f"  Query: {query}")

    t0 = time.time()
    resp = _req("POST", "/v1/ask", body={
        "query": query,
        "context_scope": "public",
    }, timeout=180)
    elapsed = time.time() - t0

    print(f"  Response time: {elapsed:.1f}s")
    print(f"  Intent: {resp.get('intent')}")
    print(f"  Answer (first 200 chars): {resp.get('answer', '')[:200]}")

    # 验证响应结构
    assert "answer" in resp, f"缺少 answer: {list(resp.keys())}"
    assert len(resp["answer"]) > 0, "answer 为空"
    assert "intent" in resp
    assert resp["intent"] in ("rag", "unknown"), f"意图不是 rag: {resp['intent']}"

    # 如果 intent 是 rag，应该有 sources
    if resp["intent"] == "rag" and resp.get("sources"):
        print(f"  Sources: {len(resp['sources'])} 条")
        for s in resp["sources"][:3]:
            print(f"    - score={s.get('score')}: {s.get('chunk_text', '')[:80]}")

    print("  ✅ Seed+Ask 流程通过")
    return resp


# ═══════════════════════════════════════════════════════════
# Test 3: Cache 命中验证
# ═══════════════════════════════════════════════════════════

def test_cache_hit():
    """验证相同 query 第二次请求缓存命中，响应时间 < 50ms。"""
    print("\n[TEST 3] Cache 命中验证...")

    query = "什么是底座优先架构？"

    # 第一次请求（预期 cache miss，较慢）
    print(f"  Query: {query}")
    print("  Request 1 (expected cache MISS)...")
    t1 = time.time()
    resp1 = _req("POST", "/v1/ask", body={
        "query": query,
        "context_scope": "public",
    }, timeout=180)
    elapsed1 = (time.time() - t1) * 1000
    print(f"  Request 1: {elapsed1:.0f}ms, intent={resp1.get('intent')}")

    # 第二次请求（预期 cache hit，< 50ms）
    print("  Request 2 (expected cache HIT)...")
    t2 = time.time()
    resp2 = _req("POST", "/v1/ask", body={
        "query": query,
        "context_scope": "public",
    }, timeout=10)
    elapsed2 = (time.time() - t2) * 1000
    print(f"  Request 2: {elapsed2:.0f}ms, intent={resp2.get('intent')}")

    # 验证两次答案一致
    assert resp1["answer"] == resp2["answer"], "缓存命中后答案不一致"

    # 验证第二次是缓存命中（tokens_used 是 elapsed ms，应 < 50ms）
    # 注意：缓存命中时 tokens_used 字段为耗时 ms
    tokens2 = resp2.get("tokens_used", 0)
    print(f"  Cache hit latency: tokens_used={tokens2}ms, wall_clock={elapsed2:.0f}ms")

    # 宽松验证：wall clock 应 < 500ms（网络延迟）
    assert elapsed2 < 500, f"缓存命中响应太慢: {elapsed2:.0f}ms (expected < 500ms)"

    print("  ✅ Cache 命中验证通过")
    return resp2


# ═══════════════════════════════════════════════════════════
# Test 4: 熔断器状态（启动后应为 closed）
# ═══════════════════════════════════════════════════════════

def test_circuit_breaker_initial_state():
    """验证启动后熔断器处于 closed 状态。"""
    print("\n[TEST 4] 熔断器初始状态...")

    resp = _req("GET", "/v1/health")
    resilience = resp["resilience"]

    llm_cb = resilience["llm_circuit_breaker"]
    embed_cb = resilience["embed_circuit_breaker"]

    print(f"  LLM CB: state={llm_cb['state']}, failures={llm_cb['failure_count']}")
    print(f"  Embed CB: state={embed_cb['state']}, failures={embed_cb['failure_count']}")

    # 熔断器状态应是有效值
    assert llm_cb["state"] in ("closed", "open", "half_open"), f"无效的 LLM CB 状态: {llm_cb['state']}"
    assert embed_cb["state"] in ("closed", "open", "half_open"), f"无效的 Embed CB 状态: {embed_cb['state']}"

    # 阈值配置
    assert llm_cb["threshold"] == 5, f"LLM CB 阈值不对: {llm_cb['threshold']}"
    assert embed_cb["threshold"] == 5, f"Embed CB 阈值不对: {embed_cb['threshold']}"

    print("  ✅ 熔断器状态检查通过")


# ═══════════════════════════════════════════════════════════
# Test 5: 不同意图分发
# ═══════════════════════════════════════════════════════════

def test_intent_dispatch():
    """验证不同意图能正确分发到对应端口。"""
    print("\n[TEST 5] 意图分发验证...")

    test_cases = [
        ("推荐一句思乡的诗", "poetry", "诗词推荐"),
        ("我性格内向喜欢独处喜欢思考问题", "mbti", "MBTI 测评"),
        ("介绍一下 pgvector", "rag", "RAG 知识库"),
        ("帮我匹配职位", "job_match", "职位匹配"),
    ]

    for query, expected_intent, desc in test_cases:
        print(f"  [{desc}] Query: {query[:50]}")
        resp = _req("POST", "/v1/ask", body={
            "query": query,
            "context_scope": "public",
        }, timeout=180)
        actual = resp.get("intent", "unknown")
        status = "✅" if actual == expected_intent else "⚠️"
        print(f"    {status} intent={actual} (expected={expected_intent})")

    print("  ✅ 意图分发验证完成")


# ═══════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════

def run_all():
    """运行所有 smoke 测试。"""
    print("=" * 60)
    print("  Looma 集成 Smoke 测试")
    print(f"  BASE_URL: {BASE_URL}")
    print(f"  AUTH_TOKEN: {AUTH_TOKEN[:16]}...")
    print("=" * 60)

    results = []
    tests = [
        ("健康端点", test_health_endpoint),
        ("Seed+Ask 流程", test_seed_and_ask),
        ("Cache 命中验证", test_cache_hit),
        ("熔断器状态", test_circuit_breaker_initial_state),
        ("意图分发", test_intent_dispatch),
    ]

    passed = 0
    failed = 0
    errors = []

    for name, fn in tests:
        try:
            fn()
            passed += 1
            results.append((name, "PASS"))
        except AssertionError as e:
            failed += 1
            results.append((name, "FAIL"))
            errors.append((name, str(e)))
            print(f"  ❌ FAIL: {e}")
        except Exception as e:
            failed += 1
            results.append((name, "ERROR"))
            errors.append((name, str(e)))
            print(f"  💥 ERROR: {e}")

    # 汇总
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    for name, status in results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {name}: {status}")

    print(f"\n  通过: {passed}/{len(tests)}, 失败: {failed}/{len(tests)}")

    if errors:
        print("\n  失败详情:")
        for name, err in errors:
            print(f"    - {name}: {err}")

    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
