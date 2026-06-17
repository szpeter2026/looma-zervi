"""验证 Tatha Chroma 数据可访问性"""
import chromadb

PATH = "D:/surface-zervi/GitHub/szjason72/Tatha/.data/chroma/poetry_full"

client = chromadb.PersistentClient(path=PATH)
collection = client.get_collection("poetry_full")
total = collection.count()
print(f"Collection: poetry_full")
print(f"Total embeddings: {total}")

# 抽样
sample = collection.get(limit=5, include=["documents", "metadatas", "embeddings"])
print(f"\n--- 抽样 5 条 ---")
for i, (doc, meta, emb) in enumerate(zip(
    sample["documents"], sample["metadatas"], sample["embeddings"]
)):
    title = meta.get("title", "?")
    author = meta.get("author", "?")
    dynasty = meta.get("dynasty", "?")
    dim = len(emb) if emb is not None else 0
    print(f"[{i+1}] 《{title}》— {author} ({dynasty})")
    print(f"    向量维度: {dim}d")
    print(f"    正文: {doc[:80]}...")
    print()

# 语义搜索测试
print("--- 语义搜索测试 ---")
results = collection.query(query_texts=["大漠孤烟直，长河落日圆"], n_results=3)
for i, (doc_id, doc, meta, dist) in enumerate(zip(
    results["ids"][0], results["documents"][0],
    results["metadatas"][0], results["distances"][0]
)):
    print(f"[{i+1}] 《{meta.get('title','?')}》— {meta.get('author','?')} | 距离: {dist:.4f}")
    print(f"    {doc[:60]}...")
    print()

print("✅ Chroma 数据验证完成")
