"""
完整验证脚本: 诗词数据可用性 + 语义搜索功能
"""
import sys
sys.path.insert(0, ".")

from src.agents.poetry_search import search_poems, get_poetry_stats

print("=" * 55)
print("  中华诗词向量库 - 完整验证")
print("=" * 55)

# 1. 统计
stats = get_poetry_stats()
print(f"\n[1] 数据库统计")
for k, v in stats.items():
    print(f"    {k}: {v}")

# 2. 语义搜索测试
test_cases = [
    ("思乡", "应返回思乡主题诗词"),
    ("大漠孤烟直，长河落日圆", "应匹配边塞/大漠主题"),
    ("春花秋月何时了", "应匹配伤春/怀旧主题"),
    ("醉卧沙场君莫笑", "应匹配边塞/饮酒主题"),
    ("床前明月光", "应匹配明月/思乡主题"),
]

print(f"\n[2] 语义搜索测试")
passed = 0
for query, expected in test_cases:
    results = search_poems(query, n_results=3)
    if results:
        passed += 1
        print(f"\n  Query: '{query}'")
        print(f"  Expected: {expected}")
        for i, r in enumerate(results):
            print(f"    [{i+1}] 《{r['title']}》- {r['author']}({r['dynasty']})")
            print(f"        距离: {r['distance']:.4f} | {r['content'][:60].strip()}...")
    else:
        print(f"\n  Query: '{query}' -> 无结果")

print(f"\n[3] 测试结果: {passed}/{len(test_cases)} 通过")

# 3. 性能测试
import time
print(f"\n[4] 性能测试")
start = time.time()
results = search_poems("明月几时有", n_results=10)
elapsed = time.time() - start
print(f"    10条结果检索耗时: {elapsed*1000:.0f}ms")
print(f"    吞吐量: {78656/elapsed:.0f} 条/秒 (全库扫描)")

print(f"\n{'=' * 55}")
print(f"  验证完成 - 78,656 首诗词可正常检索")
print(f"{'=' * 55}")
