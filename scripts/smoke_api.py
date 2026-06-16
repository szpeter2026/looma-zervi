"""
smoke_api.py — FastAPI + LiteLLM 端到端烟测
==========================================
验证：
1. FastAPI 能启动 @ 127.0.0.1:8010
2. /v1/health 返回 ok
3. /v1/ask 执行 RAG 检索 + LLM 生成回答（LiteLLM → ollama/qwen2.5-coder:1.5b）
4. 返回的回答包含检索到的来源（source_nodes）

前置：
    - PG + pgvector 运行（docker-compose up -d 或本地安装）
    - Ollama 运行，qwen2.5-coder:1.5b + nomic-embed-text:latest 已 pull
    - .env 配置正确（参考 .env.example）
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROJECT = Path(__file__).resolve().parent.parent
LOOMA_PORT = int(os.getenv("LOOMA_PORT", "8010"))

# 跨平台 venv python 路径
import platform
if platform.system() == "Windows":
    VENV_PYTHON = str(PROJECT / ".venv" / "Scripts" / "python.exe")
else:
    VENV_PYTHON = str(PROJECT / ".venv" / "bin" / "python")

STATE_FILE = PROJECT / ".smoke_state_api.json"


def step(msg: str) -> None:
    print(f"\n=== {msg} ===", flush=True)


def main() -> int:
    state: dict = {"steps": {}, "verdict": "UNKNOWN"}
    t0_all = time.time()

    # 0. 清代理
    step("0. 准备环境")
    env = os.environ.copy()
    for _k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
        env.pop(_k, None)

    # 1. 启动 FastAPI 进程（新入口 src.api.app）
    step(f"1. 启动 FastAPI @ 127.0.0.1:{LOOMA_PORT}")
    t0 = time.time()
    proc = subprocess.Popen(
        [VENV_PYTHON, "-m", "uvicorn", "src.api.app:app", "--host", "127.0.0.1", "--port", str(LOOMA_PORT)],
        cwd=str(PROJECT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    state["steps"]["start_server"] = {"pid": proc.pid, "port": LOOMA_PORT}

    # 等服务器就绪（最多 10 秒）
    ready = False
    for i in range(20):
        time.sleep(0.5)
        ret = proc.poll()
        if ret is not None:
            stderr = proc.stderr.read().decode() if proc.stderr else ""
            print(f"  服务器启动失败 (exit={ret}): {stderr[:300]}")
            state["verdict"] = "FAIL"
            state["total_ms"] = int((time.time() - t0_all) * 1000)
            STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
            return 1
        try:
            import urllib.request
            req = urllib.request.Request(f"http://127.0.0.1:{LOOMA_PORT}/v1/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            pass
        print(f"  等待服务器就绪... ({i+1}/20)", flush=True)

    if not ready:
        print("  服务器 10 秒内未就绪")
        proc.terminate()
        state["verdict"] = "FAIL"
        state["total_ms"] = int((time.time() - t0_all) * 1000)
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        return 1

    state["steps"]["start_server"]["elapsed_ms"] = int((time.time() - t0) * 1000)
    print(f"  服务器就绪，耗时 {state['steps']['start_server']['elapsed_ms']}ms")

    try:
        # 2. 健康检查
        step("2. GET /v1/health")
        t0 = time.time()
        import urllib.request as _req

        with _req.urlopen(f"http://127.0.0.1:{LOOMA_PORT}/v1/health", timeout=5) as resp:
            health = json.loads(resp.read())
        state["steps"]["health"] = {
            "status": health.get("status"),
            "version": health.get("version"),
            "elapsed_ms": int((time.time() - t0) * 1000),
        }
        print(f"  status={health.get('status')}, version={health.get('version')}")

        # 3. RAG 问答
        step("3. POST /v1/ask（RAG 检索 + LLM 生成）")
        t0 = time.time()
        payload = json.dumps({
            "query": "底座优先架构是什么？",
            "execution_hint": "auto",
            "context_scope": "public",
        }).encode("utf-8")
        req = _req.Request(
            f"http://127.0.0.1:{LOOMA_PORT}/v1/ask",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _req.urlopen(req, timeout=60) as resp:
            ask_resp = json.loads(resp.read())

        state["steps"]["ask"] = {
            "query": "底座优先架构是什么？",
            "answer_preview": ask_resp.get("answer", "")[:120],
            "source_count": len(ask_resp.get("sources", [])),
            "intent": ask_resp.get("intent"),
            "executed_on": ask_resp.get("executed_on"),
            "elapsed_ms": int((time.time() - t0) * 1000),
        }
        print(f"  answer: {ask_resp.get('answer', '')[:150]}...")
        print(f"  sources: {len(ask_resp.get('sources', []))} 条")
        print(f"  intent: {ask_resp.get('intent')}, executed_on: {ask_resp.get('executed_on')}")

        # 4. 校验
        step("4. 校验")
        answer = ask_resp.get("answer", "")
        sources = ask_resp.get("sources", [])

        checks = []
        checks.append(("有回答内容", len(answer) > 10))
        checks.append(("有检索来源", len(sources) > 0))
        checks.append(("回答与问题相关", len(answer) > 30 and ("底座" in answer or "架构" in answer or "pgvector" in answer.lower())))
        checks.append(("intent 字段存在", ask_resp.get("intent") is not None))
        checks.append(("executed_on 字段存在", ask_resp.get("executed_on") is not None))

        all_pass = all(passed for _, passed in checks)
        for label, passed in checks:
            print(f"  {'PASS' if passed else 'FAIL'} {label}")

        verdict = "PASS" if all_pass else "FAIL"
        state["verdict"] = verdict

    finally:
        # 5. 关闭服务器
        step("5. 关闭服务器")
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("  已关闭")

    state["total_ms"] = int((time.time() - t0_all) * 1000)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    print(f"\n=== 状态写入 {STATE_FILE.name}  总耗时 {state['total_ms']}ms ===")
    print(f"  VERDICT: {state['verdict']}")
    return 0 if state["verdict"] == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nEXCEPTION: {type(e).__name__}: {e}", file=sys.stderr)
        raise
