"""
Looma pipeline — 报告生成器

生成日/周/月报，基于知识库统计数据。
来源：DemoPeter report_gen.py，已迁入 looma-zervi。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.core.config import get_settings


class ReportGenerator:
    """报告生成器 — 日报/周报/月报"""

    def __init__(self, reports_dir: Path | None = None):
        from src.core.config import get_settings
        settings = get_settings()
        if reports_dir is None:
            # 默认存放在项目根目录下的 reports/
            reports_dir = Path(__file__).resolve().parent.parent.parent / "reports"
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _get_stats(self) -> dict:
        """获取知识库统计"""
        try:
            from src.db.manager import DBManager
            db = DBManager()
            return db.get_stats()
        except Exception:
            return {
                "documents_total": 0,
                "documents_completed": 0,
                "documents_pending": 0,
                "chunks_total": 0,
                "total_characters": 0,
                "queries_total": 0,
            }

    def generate_daily(self) -> str:
        """生成日报"""
        today = datetime.now().strftime("%Y-%m-%d")
        stats = self._get_stats()
        recent = self._get_recent_queries()

        report = f"""# 📊 Looma 日报 — {today}

## 知识库概况
| 指标 | 数值 |
|------|------|
| 文档总数 | {stats.get('documents_total', 0)} |
| 已处理 | {stats.get('documents_completed', 0)} |
| 分块总数 | {stats.get('chunks_total', 0)} |
| 总字符数 | {stats.get('total_characters', 0):,} |
| 查询总数 | {stats.get('queries_total', 0)} |

## 今日查询
{self._format_queries(recent)}

---
*自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        path = self.reports_dir / f"daily_{today}.md"
        path.write_text(report, encoding="utf-8")
        return str(path)

    def generate_weekly(self) -> str:
        """生成周报"""
        week = datetime.now().strftime("%Y-W%W")
        report = f"""# 📈 Looma 周报 — {week}

## 知识库统计
{self._format_stats_table()}

## 本周新增
- 文档：待补充
- 查询：待统计

---
*自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        path = self.reports_dir / f"weekly_{week}.md"
        path.write_text(report, encoding="utf-8")
        return str(path)

    def generate_monthly(self) -> str:
        """生成月报"""
        month = datetime.now().strftime("%Y-%m")
        report = f"""# 📅 Looma 月报 — {month}

## 知识库统计总览
{self._format_stats_table()}

## 月度总结
- 知识库持续增长中

---
*自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        path = self.reports_dir / f"monthly_{month}.md"
        path.write_text(report, encoding="utf-8")
        return str(path)

    def _format_stats_table(self) -> str:
        stats = self._get_stats()
        return f"""| 指标 | 数值 |
|------|------|
| 文档总数 | {stats.get('documents_total', 0)} |
| 已处理文档 | {stats.get('documents_completed', 0)} |
| 待处理文档 | {stats.get('documents_pending', 0)} |
| 分块总数 | {stats.get('chunks_total', 0)} |
| 总字符数 | {stats.get('total_characters', 0):,} |
| 历史查询 | {stats.get('queries_total', 0)} |"""

    def _get_recent_queries(self, limit: int = 10) -> list[dict]:
        try:
            from src.db.manager import DBManager
            db = DBManager()
            return db.get_recent_queries(limit=limit)
        except Exception:
            return []

    @staticmethod
    def _format_queries(queries: list[dict]) -> str:
        if not queries:
            return "暂无查询记录"
        return "\n".join(
            f"- [{q.get('created_at', '')[:16]}] {q.get('query_text', '')[:80]} ({q.get('provider', '')}, {q.get('response_time_ms', 0):.0f}ms)"
            for q in queries[:10]
        )