"""Looma 并发容量测试脚本

用法:
  python scripts/concurrency_test.py --url http://127.0.0.1:5200/v1/ask \
      --token token-b658c985 --concurrency 5 --requests 20

本脚本使用多线程并发发送 /v1/ask 请求，测量响应延迟与成功率。
适合内测环境的初步并发评估。
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import sys
import threading
import time
import urllib.request
from typing import Any


def percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)
    return s[int(k)] if f == c else s[f] * (c - k) + s[c] * (k - f)


def wait_ready(url: str, timeout: int = 60) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = urllib.request.urlopen(url, timeout=3)
            if r.status == 200:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


def send_request(url: str, auth_token: str, query: str, timeout: int = 120) -> tuple[float, bool, int, str]:
    payload = json.dumps({"query": query, "context_scope": "public"}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers=headers,
        method="POST",
    )
    t0 = time.time()
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        elapsed = (time.time() - t0) * 1000
        body = json.loads(resp.read())
        success = resp.status == 200
        return elapsed, success, resp.status, body.get("answer", "")[:100]
    except Exception as exc:
        elapsed = (time.time() - t0) * 1000
        return elapsed, False, getattr(exc, 'code', 0) or 0, str(exc)


def run_load_test(
    url: str,
    auth_token: str,
    concurrency: int,
    total_requests: int,
    ready_url: str | None,
) -> dict[str, Any]:
    if ready_url:
        print(f"Waiting for service ready at {ready_url} ...")
        if not wait_ready(ready_url):
            print("WARNING: service did not become ready in time, continuing anyway")

    print(f"Starting concurrency test: concurrency={concurrency}, total_requests={total_requests}")
    queries = [f"内测并发测试 question {i} {time.time_ns() % 100000}" for i in range(total_requests)]
    durations: list[float] = []
    failures = 0
    statuses: dict[int, int] = {}
    errors: dict[str, int] = {}
    lock = threading.Lock()

    def task(query: str) -> None:
        nonlocal failures
        elapsed, ok, status, detail = send_request(url, auth_token, query)
        with lock:
            durations.append(elapsed)
            statuses[status] = statuses.get(status, 0) + 1
            if not ok:
                failures += 1
                errors[detail] = errors.get(detail, 0) + 1

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        list(executor.map(task, queries))
    duration = time.time() - start

    ok_durations = [d for d in durations if d >= 0]
    success_count = total_requests - failures
    print("\n=== Concurrency Test Summary ===")
    print(f"Total requests: {total_requests}")
    print(f"Success: {success_count}")
    print(f"Failures: {failures}")
    print(f"Elapsed: {duration:.1f}s")
    print(f"Throughput: {total_requests / max(duration, 1):.1f} req/s")
    if ok_durations:
        print(f"avg latency: {sum(ok_durations) / len(ok_durations) / 1000:.3f}s")
        print(f"p50: {percentile(ok_durations, 50) / 1000:.3f}s")
        print(f"p90: {percentile(ok_durations, 90) / 1000:.3f}s")
        print(f"p95: {percentile(ok_durations, 95) / 1000:.3f}s")
        print(f"p99: {percentile(ok_durations, 99) / 1000:.3f}s")
    print("Status codes:")
    for status, count in sorted(statuses.items()):
        print(f"  {status}: {count}")
    if errors:
        print("Top failure reasons:")
        for err, count in sorted(errors.items(), key=lambda item: item[1], reverse=True)[:5]:
            print(f"  {count}x {err}")

    result: dict[str, Any] = {
        "total_requests": total_requests,
        "success": success_count,
        "failures": failures,
        "elapsed_s": round(duration, 2),
        "throughput_rps": round(total_requests / max(duration, 1), 2),
        "status_codes": {str(k): v for k, v in sorted(statuses.items())},
        "error_rate": round(failures / total_requests, 4) if total_requests else 0,
    }
    if ok_durations:
        result["latency_ms"] = {
            "avg": round(sum(ok_durations) / len(ok_durations), 1),
            "p50": round(percentile(ok_durations, 50), 1),
            "p90": round(percentile(ok_durations, 90), 1),
            "p95": round(percentile(ok_durations, 95), 1),
            "p99": round(percentile(ok_durations, 99), 1),
        }
    if errors:
        result["top_errors"] = [
            {"error": err, "count": count}
            for err, count in sorted(errors.items(), key=lambda item: item[1], reverse=True)[:5]
        ]
    return result


def prepare_ask_test_token(base_url: str) -> str:
    """Register a throwaway user and grant ask_rag consent for load testing."""
    email = f"baseline-{int(time.time())}@test.local"
    register_payload = json.dumps(
        {"email": email, "password": "baseline-test-pass", "name": "BaselineTest"}
    ).encode("utf-8")
    register_req = urllib.request.Request(
        f"{base_url}/v1/auth/register",
        data=register_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(register_req, timeout=30) as resp:
        token = json.loads(resp.read())["access_token"]

    grant_payload = json.dumps({"scope": "ask_rag"}).encode("utf-8")
    grant_req = urllib.request.Request(
        f"{base_url}/v1/compliance/consent/grant",
        data=grant_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(grant_req, timeout=30):
        pass
    return token


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Looma 并发容量测试脚本")
    parser.add_argument("--url", default="http://127.0.0.1:5200/v1/ask", help="目标 /v1/ask URL")
    parser.add_argument("--token", default="", help="Bearer token (omit to auto-register test user)")
    parser.add_argument("--concurrency", type=int, default=5, help="并发线程数")
    parser.add_argument("--requests", type=int, default=20, help="总请求数")
    parser.add_argument("--ready-url", default="http://127.0.0.1:5200/health", help="服务就绪检测 URL")
    parser.add_argument("--json-output", default="", help="Write machine-readable results to this file")
    parser.add_argument("--prepare-token", action="store_true", help="Register user + grant ask_rag consent")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.url.rsplit("/v1/ask", 1)[0]
    token = args.token
    if args.prepare_token or not token:
        print("Preparing test user with ask_rag consent...")
        token = prepare_ask_test_token(base_url)
    result = run_load_test(args.url, token, args.concurrency, args.requests, args.ready_url)
    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"Results written to {args.json_output}")
    return 0 if result["failures"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())