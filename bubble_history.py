"""AI泡沫分数的可审计历史序列与每日快照更新。"""

from datetime import date
from pathlib import Path
import json


HISTORY_FILE = Path(__file__).parent / "knowledge" / "ai_bubble_history.json"


def load_bubble_history():
    with HISTORY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    data["snapshots"] = sorted(data["snapshots"], key=lambda item: item["date"])
    return data


def stage_from_score(score):
    if score < 35:
        return "资本验证"
    if score < 62:
        return "繁荣扩张"
    if score < 84:
        return "泡沫扩张后期／盈利验证拐点"
    return "顶部与去杠杆风险区"


def append_news_snapshot(report, snapshot_date=None):
    """把新闻聚合结果转成当日模型快照；同一天重复运行时覆盖旧值。"""
    history = load_bubble_history()
    snapshots = history["snapshots"]
    snapshot_date = snapshot_date or report.get("as_of_date") or date.today().isoformat()
    previous = next((item for item in reversed(snapshots) if item["date"] < snapshot_date), snapshots[-1])
    diagnosis_file = Path(__file__).parent / "knowledge" / "ai_bubble_diagnosis.json"
    if diagnosis_file.exists():
        with diagnosis_file.open("r", encoding="utf-8") as file:
            current_diagnosis = json.load(file)
        if current_diagnosis.get("as_of_date") == snapshot_date:
            previous = {"score": current_diagnosis["stage_score"]}
    pressure = float(report.get("bubble_pressure", 0))
    delta = max(-3, min(3, round(pressure)))
    score = max(0, min(100, previous["score"] + delta))

    direction = f"升温{abs(delta)}分" if delta > 0 else f"降温{abs(delta)}分" if delta < 0 else "基本不变"
    drivers = report.get("bubble_drivers", [])[:4] or ["当日标题未触发显著泡沫升温或降温关键词"]
    snapshot = {
        "date": snapshot_date,
        "score": score,
        "stage": stage_from_score(score),
        "confidence": "中低" if report.get("news_count", 0) < 15 else "中等",
        "snapshot_type": "每日新闻连续更新",
        "judgment": f"相对上一期泡沫热度{direction}。{report.get('bubble_summary', report.get('summary', ''))}",
        "drivers": drivers,
        "source_title": f"每日新闻聚合｜{report.get('provider', '公开新闻源')}",
        "source_url": report.get("source_url", ""),
        "news_count": report.get("news_count", 0),
        "change": delta,
    }
    snapshots = [item for item in snapshots if item["date"] != snapshot_date] + [snapshot]
    history["snapshots"] = sorted(snapshots, key=lambda item: item["date"])
    with HISTORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)
    return snapshot
