"""DeepSeek uncached 负载测试 — 等效于 k6，输出 JSON 摘要
用法: python scripts/load_test_deepseek.py [iterations]
"""
import urllib.request
import json
import time
import sys
import statistics
import math

BASE = "http://127.0.0.1:8010"
# 使用 enterprise 种子用户 token（99999 配额/天）
AUTH_TOKEN = "Bearer token-b658c985"
URL = f"{BASE}/v1/ask"


def percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    f, c = math.floor(k), math.ceil(k)
    return s[int(k)] if f == c else s[f] * (c - k) + s[c] * (k - f)


def wait_ready(timeout=60):
    """等待种子知识库就绪"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = urllib.request.urlopen(f"{BASE}/v1/health", timeout=3)
            d = json.loads(r.read())
            if d.get("dependencies", {}).get("rag_index"):
                print(f"  RAG indexed ready (uptime={d['uptime_seconds']}s)", flush=True)
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def send_request(query: str) -> tuple[float, int, bool]:
    payload = json.dumps({"query": query, "context_scope": "public"}).encode()
    req = urllib.request.Request(
        URL, data=payload,
        headers={"Content-Type": "application/json", "Authorization": AUTH_TOKEN},
        method="POST",
    )
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=120)
        elapsed = (time.time() - t0) * 1000
        body = json.loads(r.read())
        return elapsed, len(body.get("answer", "")), r.status == 200
    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        print(f"  FAIL ({elapsed:.0f}ms): {e}", flush=True)
        return elapsed, 0, False


def main():
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(f"=== DeepSeek Uncached Load Test ===", flush=True)
    print(f"Iterations: {iterations} | VU: 1 | Provider: DeepSeek | Token: enterprise", flush=True)

    print("Waiting for RAG index...", flush=True)
    if not wait_ready():
        print("WARNING: RAG index not ready, proceeding anyway", flush=True)
    time.sleep(2)

    print(f"Start: {time.strftime('%H:%M:%S')}", flush=True)

    durations: list[float] = []
    answer_lens: list[int] = []
    failures = 0

    t_start = time.time()
    for i in range(iterations):
        unique = f"t{i}-{time.time_ns() % 100000}"
        query = f"Looma平台有哪些核心功能 {unique}"

        dur, ans_len, ok = send_request(query)
        durations.append(dur)
        answer_lens.append(ans_len)
        if not ok:
            failures += 1

        elapsed_total = time.time() - t_start
        ok_durs = [d for d in durations if d > 100]  # exclude 429 failures
        avg_ok = statistics.mean(ok_durs) / 1000 if ok_durs else 0
        eta = (elapsed_total / (i + 1)) * (iterations - i - 1) if i < iterations - 1 else 0
        print(f"  [{i+1:3d}/{iterations}] {dur/1000:5.1f}s  ans={ans_len}B  "
              f"avg={avg_ok:.1f}s  fail={failures}  ETA={eta:.0f}s", flush=True)

    total_time = time.time() - t_start
    ok_durs = [d for d in durations if d > 100]

    if not ok_durs:
        print("\nERROR: No successful requests!", flush=True)
        sys.exit(1)

    stats = {
        "test_config": {
            "provider": "deepseek (deepseek-v4-pro)",
            "iterations_requested": iterations,
            "iterations_succeeded": len(ok_durs),
            "concurrency": 1,
            "cache": "disabled (unique queries per iteration)",
            "auth": "enterprise (token-b658c985)",
        },
        "duration_seconds": round(total_time, 1),
        "http_req_duration_ms": {
            "min": round(min(ok_durs), 1),
            "max": round(max(ok_durs), 1),
            "avg": round(statistics.mean(ok_durs), 1),
            "med": round(statistics.median(ok_durs), 1),
            "p90": round(percentile(ok_durs, 90), 1),
            "p95": round(percentile(ok_durs, 95), 1),
            "p99": round(percentile(ok_durs, 99), 1),
        },
        "failures": failures,
        "success_rate_pct": round((iterations - failures) / iterations * 100, 1),
        "answer_length_avg": round(statistics.mean(answer_lens), 0),
    }

    output_file = "k6_deepseek_uncached.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}", flush=True)
    print(f"DONE in {total_time:.0f}s | Saved: {output_file}", flush=True)
    s = stats['http_req_duration_ms']
    print(f"requests: {len(ok_durs)}/{iterations}  failures: {failures}", flush=True)
    print(f"avg={s['avg']/1000:.2f}s  p50={s['med']/1000:.2f}s  p90={s['p90']/1000:.2f}s  "
          f"p95={s['p95']/1000:.2f}s  p99={s['p99']/1000:.2f}s", flush=True)
    print(f"min={s['min']/1000:.2f}s  max={s['max']/1000:.2f}s", flush=True)


if __name__ == "__main__":
    main()
