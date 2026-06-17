import time, traceback, importlib, sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

m2 = importlib.import_module('src.core.llm')
print('active before:', m2.get_active_provider())
llm = m2.get_llm()
for i in range(3):
    t0 = time.time()
    try:
        out = llm.complete(f"测试 deepseek 延迟 {i}")
        dt = time.time() - t0
        print(f'ok {i} t={dt:.2f}s out={str(out)[:200]}')
    except Exception:
        dt = time.time() - t0
        print(f'error {i} t={dt:.2f}s')
        traceback.print_exc()
print('active after:', m2.get_active_provider())
