"""每日新闻情报归档数据库。

数据库只保存聚合摘要、风向指标与模型结论，不保存新闻正文或文章列表。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3


ARCHIVE_DB = Path(__file__).parent / "data" / "news_archive.sqlite3"


def _connect(db_path=ARCHIVE_DB):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 15000")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_news_archive (
            report_date TEXT PRIMARY KEY,
            fetched_at TEXT NOT NULL,
            archived_at TEXT NOT NULL,
            provider TEXT NOT NULL,
            news_count INTEGER NOT NULL,
            summary TEXT NOT NULL,
            bubble_summary TEXT NOT NULL,
            bubble_pressure REAL NOT NULL,
            category_counts_json TEXT NOT NULL,
            asset_impact_json TEXT NOT NULL,
            cycle_impact_json TEXT NOT NULL,
            bubble_drivers_json TEXT NOT NULL,
            deepseek_analysis TEXT,
            deepseek_analyzed_at TEXT,
            deepseek_model TEXT,
            deepseek_evidence_count INTEGER NOT NULL DEFAULT 0,
            source_url TEXT,
            limitations_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_daily_news_fetched_at "
        "ON daily_news_archive(fetched_at DESC)"
    )
    return connection


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _from_json(value, fallback):
    try:
        return json.loads(value) if value else fallback
    except (TypeError, json.JSONDecodeError):
        return fallback


def archive_daily_report(report, db_path=ARCHIVE_DB):
    """按日期写入或更新一条摘要记录，不保存 ``articles``。"""
    if not report:
        raise ValueError("没有可归档的新闻报告。")
    report_date = report.get("as_of_date") or report["fetched_at"][:10]
    archived_at = datetime.now(timezone.utc).isoformat()
    values = {
        "report_date": report_date,
        "fetched_at": report["fetched_at"],
        "archived_at": archived_at,
        "provider": report.get("provider", "未知"),
        "news_count": int(report.get("news_count", 0)),
        "summary": report.get("summary", "暂无规则摘要。"),
        "bubble_summary": report.get("bubble_summary", "暂无泡沫增量判断。"),
        "bubble_pressure": float(report.get("bubble_pressure", 0)),
        "category_counts_json": _json(report.get("category_counts", {})),
        "asset_impact_json": _json(report.get("asset_impact", {})),
        "cycle_impact_json": _json(report.get("cycle_impact", {})),
        "bubble_drivers_json": _json(report.get("bubble_drivers", [])),
        "deepseek_analysis": report.get("deepseek_analysis"),
        "deepseek_analyzed_at": report.get("deepseek_analyzed_at"),
        "deepseek_model": report.get("deepseek_model"),
        "deepseek_evidence_count": int(report.get("deepseek_evidence_count", 0)),
        "source_url": report.get("source_url"),
        "limitations_json": _json(report.get("limitations", [])),
    }
    columns = ", ".join(values)
    placeholders = ", ".join(f":{name}" for name in values)
    updates = ", ".join(
        f"{name} = excluded.{name}" for name in values if name != "report_date"
    )
    with _connect(db_path) as connection:
        connection.execute(
            f"""
            INSERT INTO daily_news_archive ({columns})
            VALUES ({placeholders})
            ON CONFLICT(report_date) DO UPDATE SET {updates}
            """,
            values,
        )
    return report_date


def _row_to_report(row):
    if not row:
        return None
    report = {
        "as_of_date": row["report_date"],
        "fetched_at": row["fetched_at"],
        "archived_at": row["archived_at"],
        "provider": row["provider"],
        "source_url": row["source_url"],
        "news_count": row["news_count"],
        "summary": row["summary"],
        "bubble_summary": row["bubble_summary"],
        "bubble_pressure": row["bubble_pressure"],
        "category_counts": _from_json(row["category_counts_json"], {}),
        "asset_impact": _from_json(row["asset_impact_json"], {}),
        "cycle_impact": _from_json(row["cycle_impact_json"], {}),
        "bubble_drivers": _from_json(row["bubble_drivers_json"], []),
        "deepseek_analysis": row["deepseek_analysis"],
        "deepseek_analyzed_at": row["deepseek_analyzed_at"],
        "deepseek_model": row["deepseek_model"],
        "deepseek_evidence_count": row["deepseek_evidence_count"],
        "limitations": _from_json(row["limitations_json"], []),
        "articles": [],
        "is_archived": True,
    }
    return report


def load_archived_report(report_date=None, db_path=ARCHIVE_DB):
    """读取指定日期；未指定时读取数据库中最新一天。"""
    with _connect(db_path) as connection:
        if report_date:
            row = connection.execute(
                "SELECT * FROM daily_news_archive WHERE report_date = ?",
                (str(report_date),),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT * FROM daily_news_archive ORDER BY report_date DESC LIMIT 1"
            ).fetchone()
    return _row_to_report(row)


def list_archive_dates(db_path=ARCHIVE_DB, limit=1200):
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT report_date FROM daily_news_archive "
            "ORDER BY report_date DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    return [row["report_date"] for row in rows]


def archive_overview(db_path=ARCHIVE_DB):
    with _connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS day_count,
                   MIN(report_date) AS first_date,
                   MAX(report_date) AS last_date
            FROM daily_news_archive
            """
        ).fetchone()
    return dict(row)


def load_archive_series(db_path=ARCHIVE_DB, limit=365):
    """返回趋势图所需的轻量数据，不加载长文本分析。"""
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT report_date, news_count, bubble_pressure,
                   asset_impact_json, cycle_impact_json
            FROM daily_news_archive
            ORDER BY report_date DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    series = []
    for row in reversed(rows):
        asset = _from_json(row["asset_impact_json"], {})
        cycle = _from_json(row["cycle_impact_json"], {})
        series.append(
            {
                "date": row["report_date"],
                "news_count": row["news_count"],
                "bubble_pressure": row["bubble_pressure"],
                "stock": asset.get("股票", 0),
                "bond": asset.get("债券", 0),
                "gold": asset.get("黄金", 0),
                "growth": cycle.get("growth", 0),
                "inflation": cycle.get("inflation", 0),
            }
        )
    return series
