"""Looma retrieval — RAG 引擎（LlamaIndex）"""
from __future__ import annotations

from llama_index.core import VectorStoreIndex, Document
from src.core.config import get_settings
from src.retrieval.vector_store import get_vector_store


_index: VectorStoreIndex | None = None


def get_index() -> VectorStoreIndex:
    """获取全局 VectorStoreIndex（懒加载）"""
    global _index
    if _index is None:
        vs = get_vector_store()
        _index = VectorStoreIndex.from_vector_store(vs)
    return _index


def seed_knowledge() -> VectorStoreIndex:
    """种子知识库：写入几条常识数据，确保检索有内容可查"""
    import psycopg as _psycopg

    settings = get_settings()
    dsn = settings.PG_DSN

    # 幂等：表存在就清空重建
    with _psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s;",
                (settings.SCHEMA, settings.TABLE),
            )
            if cur.fetchone():
                cur.execute(f"TRUNCATE TABLE {settings.SCHEMA}.{settings.TABLE} RESTART IDENTITY;")

    docs = [
        Document(text="Looma 是一个 AI 驱动的职业发展平台，包含简历解析、职位匹配、MBTI 测评等功能。"),
        Document(text="Zervi 是 Looma 的客户端应用，支持本地优先架构，用户私有文档存储在本地 pgvector。"),
        Document(text="底座优先架构：统一向量引擎为 pgvector，统一嵌入模型为 nomic-embed-text 768d，统一检索框架为 LlamaIndex。"),
        Document(text="修订版路线五步：pgvector → nomic-embed → LlamaIndex → LiteLLM → FastAPI。"),
        Document(text="向量检索使用余弦相似度（<=> 操作符），支持 HNSW 索引加速百万级向量查询。"),
        Document(text="LiteLLM 统一所有模型调用，支持 Ollama 本地模型和 DeepSeek 云端模型无缝切换。"),
    ]

    global _index
    vs = get_vector_store()
    _index = VectorStoreIndex.from_documents(docs, vector_store=vs, show_progress=False)

    # 同时播种诗词数据
    _seed_poetry(dsn, settings)

    return _index


def _seed_poetry(dsn: str, settings) -> None:
    """播种诗词种子数据到 pgvector poetry 表（免费体验版核心卖点）。"""
    import psycopg as _psycopg

    poems = [
        ("静夜思", "李白", "唐",
         "床前明月光，疑是地上霜。举头望明月，低头思故乡。", "思乡"),
        ("登鹳雀楼", "王之涣", "唐",
         "白日依山尽，黄河入海流。欲穷千里目，更上一层楼。", "励志"),
        ("春晓", "孟浩然", "唐",
         "春眠不觉晓，处处闻啼鸟。夜来风雨声，花落知多少。", "田园"),
        ("送元二使安西", "王维", "唐",
         "渭城朝雨浥轻尘，客舍青青柳色新。劝君更尽一杯酒，西出阳关无故人。", "送别"),
        ("饮湖上初晴后雨", "苏轼", "宋",
         "水光潋滟晴方好，山色空蒙雨亦奇。欲把西湖比西子，淡妆浓抹总相宜。", "山水"),
        ("出塞", "王昌龄", "唐",
         "秦时明月汉时关，万里长征人未还。但使龙城飞将在，不教胡马度阴山。", "边塞"),
        ("游子吟", "孟郊", "唐",
         "慈母手中线，游子身上衣。临行密密缝，意恐迟迟归。谁言寸草心，报得三春晖。", "咏物"),
        ("元日", "王安石", "宋",
         "爆竹声中一岁除，春风送暖入屠苏。千门万户曈曈日，总把新桃换旧符。", "节日"),
        ("望岳", "杜甫", "唐",
         "岱宗夫如何？齐鲁青未了。造化钟神秀，阴阳割昏晓。荡胸生曾云，决眦入归鸟。会当凌绝顶，一览众山小。", "励志"),
        ("山居秋暝", "王维", "唐",
         "空山新雨后，天气晚来秋。明月松间照，清泉石上流。竹喧归浣女，莲动下渔舟。随意春芳歇，王孙自可留。", "山水"),
        ("枫桥夜泊", "张继", "唐",
         "月落乌啼霜满天，江枫渔火对愁眠。姑苏城外寒山寺，夜半钟声到客船。", "思乡"),
        ("黄鹤楼送孟浩然之广陵", "李白", "唐",
         "故人西辞黄鹤楼，烟花三月下扬州。孤帆远影碧空尽，唯见长江天际流。", "送别"),
        ("泊船瓜洲", "王安石", "宋",
         "京口瓜洲一水间，钟山只隔数重山。春风又绿江南岸，明月何时照我还。", "思乡"),
        ("凉州词", "王之涣", "唐",
         "黄河远上白云间，一片孤城万仞山。羌笛何须怨杨柳，春风不度玉门关。", "边塞"),
        ("念奴娇·赤壁怀古", "苏轼", "宋",
         "大江东去，浪淘尽，千古风流人物。故垒西边，人道是，三国周郎赤壁。乱石穿空，惊涛拍岸，卷起千堆雪。江山如画，一时多少豪杰。", "怀古"),
        ("题西林壁", "苏轼", "宋",
         "横看成岭侧成峰，远近高低各不同。不识庐山真面目，只缘身在此山中。", "哲理"),
        ("江南春", "杜牧", "唐",
         "千里莺啼绿映红，水村山郭酒旗风。南朝四百八十寺，多少楼台烟雨中。", "咏物"),
        ("渔歌子", "张志和", "唐",
         "西塞山前白鹭飞，桃花流水鳜鱼肥。青箬笠，绿蓑衣，斜风细雨不须归。", "田园"),
        ("春夜喜雨", "杜甫", "唐",
         "好雨知时节，当春乃发生。随风潜入夜，润物细无声。野径云俱黑，江船火独明。晓看红湿处，花重锦官城。", "咏物"),
        ("江雪", "柳宗元", "唐",
         "千山鸟飞绝，万径人踪灭。孤舟蓑笠翁，独钓寒江雪。", "山水"),
    ]

    try:
        with _psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                # 创建 poetry 表（若不存在）
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {settings.SCHEMA}.poetry (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        author TEXT NOT NULL,
                        dynasty TEXT NOT NULL,
                        content TEXT NOT NULL,
                        theme TEXT,
                        embedding vector({settings.EMBED_DIM})
                    );
                """)
                # 创建 HNSW 索引（若不存在）
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS poetry_embedding_idx
                    ON {settings.SCHEMA}.poetry
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
                """)
                # 幂等：清理旧种子
                cur.execute(f"DELETE FROM {settings.SCHEMA}.poetry WHERE title IN %s;",
                             (tuple(p[0] for p in poems),))

        # 逐个嵌入并写入（避免 Ollama 冷启动一次性全量超时）
        from src.core.embeddings import get_embed_model
        embed_model = get_embed_model()

        with _psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                for title, author, dynasty, content, theme in poems:
                    text_for_embed = f"《{title}》 {author} — {theme}\n{content}"
                    try:
                        emb = embed_model.get_text_embedding(text_for_embed)
                        emb_str = f"[{', '.join(str(x) for x in emb)}]"
                        cur.execute(
                            f"""INSERT INTO {settings.SCHEMA}.poetry
                                (title, author, dynasty, content, theme, embedding)
                                VALUES (%s, %s, %s, %s, %s, %s::vector)""",
                            (title, author, dynasty, content, theme, emb_str),
                        )
                    except Exception:
                        pass  # 单条失败跳过，下一条继续

        print(f"[startup] 诗词种子数据写入完成 ({len(poems)} 首)", flush=True)
    except Exception as e:
        print(f"[startup] 诗词种子数据初始化失败: {e}", flush=True)


def reset_index() -> None:
    """重置全局 index（测试用）"""
    global _index
    _index = None
