"""每日新闻情报归档数据库。

数据库保存聚合摘要、风向指标、模型结论和精简标题证据，不保存新闻正文。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3

from trend_metrics import derive_topic_metrics


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
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(daily_news_archive)")
    }
    if "evidence_articles_json" not in columns:
        connection.execute(
            "ALTER TABLE daily_news_archive "
            "ADD COLUMN evidence_articles_json TEXT NOT NULL DEFAULT '[]'"
        )
    if "topic_scores_json" not in columns:
        connection.execute(
            "ALTER TABLE daily_news_archive "
            "ADD COLUMN topic_scores_json TEXT NOT NULL DEFAULT '{}'"
        )
    if "topic_asset_impacts_json" not in columns:
        connection.execute(
            "ALTER TABLE daily_news_archive "
            "ADD COLUMN topic_asset_impacts_json TEXT NOT NULL DEFAULT '{}'"
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
    """按日期写入或更新摘要与精简标题证据，不保存新闻正文。"""
    if not report:
        raise ValueError("没有可归档的新闻报告。")
    report_date = report.get("as_of_date") or report["fetched_at"][:10]
    archived_at = datetime.now(timezone.utc).isoformat()
    derived_scores, derived_asset_impacts = derive_topic_metrics(report.get("articles", []))
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
        "topic_scores_json": _json(report.get("topic_scores") or derived_scores),
        "topic_asset_impacts_json": _json(
            report.get("topic_asset_impacts") or derived_asset_impacts
        ),
        "asset_impact_json": _json(report.get("asset_impact", {})),
        "cycle_impact_json": _json(report.get("cycle_impact", {})),
        "bubble_drivers_json": _json(report.get("bubble_drivers", [])),
        "deepseek_analysis": report.get("deepseek_analysis"),
        "deepseek_analyzed_at": report.get("deepseek_analyzed_at"),
        "deepseek_model": report.get("deepseek_model"),
        "deepseek_evidence_count": int(report.get("deepseek_evidence_count", 0)),
        "source_url": report.get("source_url"),
        "limitations_json": _json(report.get("limitations", [])),
        "evidence_articles_json": _json(
            [
                {
                    key: article.get(key)
                    for key in (
                        "title",
                        "source",
                        "published_at",
                        "url",
                        "category",
                        "impact_summary",
                        "asset_impact",
                        "cycle_impact",
                        "relevance_score",
                    )
                }
                for article in report.get("articles", [])[:60]
            ]
        ),
    }
    columns = ", ".join(values)
    placeholders = ", ".join(f":{name}" for name in values)
    protected = {
        "deepseek_analysis",
        "deepseek_analyzed_at",
        "deepseek_model",
        "deepseek_evidence_count",
    }
    update_parts = []
    for name in values:
        if name == "report_date":
            continue
        if name in protected:
            update_parts.append(
                f"{name} = CASE "
                "WHEN excluded.deepseek_analysis IS NOT NULL "
                "AND TRIM(excluded.deepseek_analysis) != '' "
                f"THEN excluded.{name} ELSE daily_news_archive.{name} END"
            )
        else:
            update_parts.append(f"{name} = excluded.{name}")
    updates = ", ".join(update_parts)
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
        "topic_scores": _from_json(row["topic_scores_json"], {}),
        "topic_asset_impacts": _from_json(row["topic_asset_impacts_json"], {}),
        "asset_impact": _from_json(row["asset_impact_json"], {}),
        "cycle_impact": _from_json(row["cycle_impact_json"], {}),
        "bubble_drivers": _from_json(row["bubble_drivers_json"], []),
        "deepseek_analysis": row["deepseek_analysis"],
        "deepseek_analyzed_at": row["deepseek_analyzed_at"],
        "deepseek_model": row["deepseek_model"],
        "deepseek_evidence_count": row["deepseek_evidence_count"],
        "limitations": _from_json(row["limitations_json"], []),
        "articles": _from_json(row["evidence_articles_json"], []),
        "is_archived": True,
    }
    return report


def list_reports_needing_analysis(db_path=ARCHIVE_DB, limit=30):
    """返回已有标题证据但尚无DeepSeek结论的日期，供定时任务自动补齐。"""
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM daily_news_archive
            WHERE (deepseek_analysis IS NULL OR TRIM(deepseek_analysis) = '')
              AND evidence_articles_json != '[]'
            ORDER BY report_date DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    return [_row_to_report(row) for row in rows]


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


def load_trend_history(db_path=ARCHIVE_DB, limit=1200):
    """读取已经归档的真实主题与分主题资产评分；缺失字段保持缺失。"""
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT report_date, topic_scores_json, topic_asset_impacts_json
            FROM daily_news_archive
            ORDER BY report_date ASC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    return [
        {
            "date": row["report_date"],
            "topics": _from_json(row["topic_scores_json"], {}),
            "asset_impacts": _from_json(row["topic_asset_impacts_json"], {}),
        }
        for row in rows
        if row["topic_scores_json"] != "{}" or row["topic_asset_impacts_json"] != "{}"
    ]
