"""
诗词数据导入脚本：Tatha Chroma (384d) → looma-zervi pgvector

用法:
  1. 启动 pgvector: docker compose up -d pgvector
  2. 运行: python scripts/import_poetry.py

注意:
  - Chroma 中 embeddings 为 384d (all-MiniLM-L6-v2 风格)
  - looma-zervi 默认 EMBED_DIM=768 (nomic-embed-text)
  - 因此需在 .env 中设置 EMBED_DIM=384 并更换 embedding 模型
  - 或者重新 embedding 所有诗词为 768d（本脚本也支持）
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import chromadb
import psycopg
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

# ====== 配置 ======
CHROMA_PATH = "D:/surface-zervi/GitHub/szjason72/Tatha/.data/chroma/poetry_full"
CHROMA_COLLECTION = "poetry_full"

# PG 配置（从环境变量或默认值）
PG_HOST = os.getenv("PG_HOST", "127.0.0.1")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
PG_DATABASE = os.getenv("PG_DATABASE", "looma")
PG_SCHEMA = os.getenv("PG_SCHEMA", "looma")

# 导入选项
BATCH_SIZE = 1000
DRY_RUN = "--dry-run" in sys.argv
SKIP_TABLE = "--skip-table" in sys.argv

# ====== 主逻辑 ======
def main():
    print("=" * 60)
    print("诗词数据导入: Chroma → pgvector")
    print("=" * 60)

    # 1. 连接 Chroma 源
    print(f"\n[1/5] 连接 Chroma 源: {CHROMA_PATH}")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_collection(CHROMA_COLLECTION)
    total = collection.count()
    print(f"  源数据: {total} 条 embeddings")

    # 获取一条样本确认维度
    sample = collection.get(limit=1, include=["embeddings", "metadatas"])
    embed_dim = len(sample["embeddings"][0])
    print(f"  向量维度: {embed_dim}d")
    print(f"  Metadata 字段: {list(sample['metadatas'][0].keys())}")

    # 2. 连接 PG
    dsn = f"host={PG_HOST} port={PG_PORT} user={PG_USER} password={PG_PASSWORD} dbname={PG_DATABASE}"
    print(f"\n[2/5] 连接 PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")

    try:
        conn = psycopg.connect(dsn, autocommit=True)
        print("  连接成功")
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        print("\n  请先启动 pgvector:")
        print("    cd looma-zervi && docker compose up -d pgvector")
        sys.exit(1)

    # 3. 创建 schema 和表
    print(f"\n[3/5] 准备数据库结构 (schema={PG_SCHEMA})")

    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PG_SCHEMA};")

        if not SKIP_TABLE:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {PG_SCHEMA}.poetry (
                    id          BIGSERIAL PRIMARY KEY,
                    title       TEXT,
                    author      TEXT,
                    dynasty     TEXT,
                    content     TEXT,
                    embedding   vector({embed_dim})
                );
            """)
            print(f"  表 {PG_SCHEMA}.poetry 已就绪 (vector({embed_dim}))")

            # 检查现有数据
            cur.execute(f"SELECT COUNT(*) FROM {PG_SCHEMA}.poetry;")
            existing = cur.fetchone()[0]
            if existing > 0:
                print(f"  ⚠️ 表中已有 {existing} 条数据")
                if "--force" not in sys.argv:
                    print("  使用 --force 清空重导，或 --skip-table 跳过建表")
                    conn.close()
                    return
                cur.execute(f"TRUNCATE {PG_SCHEMA}.poetry RESTART IDENTITY;")
                print(f"  已清空旧数据")

        # 创建索引
        try:
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_poetry_embedding
                ON {PG_SCHEMA}.poetry
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 200);
            """)
            print("  索引 idx_poetry_embedding 已就绪")
        except Exception as e:
            print(f"  ⚠️ 索引创建跳过: {e}")

    if DRY_RUN:
        print("\n  [DRY RUN] 跳过实际导入")
        conn.close()
        return

    # 4. 批量导入
    print(f"\n[4/5] 开始导入 (批次: {BATCH_SIZE}/批)")

    offset = 0
    imported = 0
    errors = 0

    while offset < total:
        batch = collection.get(
            limit=BATCH_SIZE,
            offset=offset,
            include=["embeddings", "metadatas", "documents"]
        )

        rows = []
        for i in range(len(batch["ids"])):
            meta = batch["metadatas"][i] or {}
            emb = batch["embeddings"][i]
            doc = batch["documents"][i] or ""

            # 将 numpy array 转为 pgvector 兼容格式
            emb_str = f"[{', '.join(str(float(x)) for x in emb)}]"
            rows.append((
                meta.get("title", ""),
                meta.get("author", ""),
                meta.get("dynasty", ""),
                doc,
                emb_str,
            ))

        try:
            with conn.cursor() as cur:
                cur.executemany(
                    f"""
                    INSERT INTO {PG_SCHEMA}.poetry (title, author, dynasty, content, embedding)
                    VALUES (%s, %s, %s, %s, %s::vector)
                    """,
                    rows
                )
            imported += len(rows)
        except Exception as e:
            errors += len(rows)
            print(f"  ❌ 批次 {offset}-{offset+BATCH_SIZE} 失败: {e}")

        offset += BATCH_SIZE
        pct = min(100, int(imported / total * 100))
        print(f"  进度: {imported}/{total} ({pct}%)", end="\r")

    print(f"\n  完成: {imported} 条导入成功, {errors} 条失败")

    # 5. 验证
    print(f"\n[5/5] 验证数据完整性")
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {PG_SCHEMA}.poetry;")
        count = cur.fetchone()[0]
        print(f"  pgvector 记录数: {count}")

        # 抽样验证
        cur.execute(f"""
            SELECT title, author, dynasty, vector_dims(embedding)
            FROM {PG_SCHEMA}.poetry
            LIMIT 3;
        """)
        print("\n  抽样验证:")
        for row in cur.fetchall():
            print(f"    《{row[0]}》— {row[1]} ({row[2]}) | 维度: {row[3]}d")

    conn.close()
    print(f"\n{'=' * 60}")
    print("导入完成！")
    print(f"{'=' * 60}")
    print(f"\n下一步:")
    print(f"  1. 确保 .env 中 EMBED_DIM={embed_dim}")
    print(f"  2. 确保 EMBED_MODEL 兼容 {embed_dim}d 向量")
    print(f"  3. 运行 poetry_search 验证检索")


if __name__ == "__main__":
    main()
