"""历史技术泡沫的可审计锚点、插值序列与生命周期比较。"""

from pathlib import Path
import json

import pandas as pd


ANALOGS_FILE = Path(__file__).parent / "knowledge" / "technology_bubble_analogs.json"


def load_technology_bubbles():
    with ANALOGS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _interpolated_record(bubble, year):
    anchors = bubble["anchors"]
    exact = next((item for item in anchors if item["year"] == year), None)
    if exact:
        return {**exact, "is_anchor": True, "evidence_year": exact["year"]}

    before = max((item for item in anchors if item["year"] < year), key=lambda item: item["year"])
    after = min((item for item in anchors if item["year"] > year), key=lambda item: item["year"])
    span = after["year"] - before["year"]
    ratio = (year - before["year"]) / span
    score = round(before["score"] + ratio * (after["score"] - before["score"]), 1)
    direction = "升温" if after["score"] > before["score"] else "降温" if after["score"] < before["score"] else "横盘"
    return {
        "year": year,
        "score": score,
        "phase": f"{before['phase']} → {after['phase']}",
        "event": f"锚点之间的模型{direction}",
        "rationale": f"在{before['year']}年与{after['year']}年证据锚点间进行线性插值；不是该年的独立历史统计。",
        "source_url": before["source_url"],
        "is_anchor": False,
        "evidence_year": before["year"],
    }


def bubble_series(bubble):
    rows = []
    for year in range(bubble["start_year"], bubble["end_year"] + 1):
        row = _interpolated_record(bubble, year)
        rows.append({
            **row,
            "id": bubble["id"],
            "name": bubble["name"],
            "short_name": bubble["short_name"],
            "color": bubble["color"],
            "relative_year": year - bubble["capital_acceleration_year"],
            "confidence": bubble["confidence"],
            "classification": bubble["classification"],
        })
    return pd.DataFrame(rows)


def all_bubble_series():
    payload = load_technology_bubbles()
    frames = [bubble_series(bubble) for bubble in payload["bubbles"]]
    return payload, pd.concat(frames, ignore_index=True)


def get_bubble(bubble_id):
    payload = load_technology_bubbles()
    return next(item for item in payload["bubbles"] if item["id"] == bubble_id)


def ai_historical_conclusion(current_score=76):
    if current_score >= 84:
        return "AI已进入与铁路1845年、互联网2000年更接近的狂热顶部区，重点不再是追逐叙事，而是防范融资反转和估值压缩。"
    if current_score >= 62:
        return "AI更接近铁路1843年前后与互联网1997—1999年的资本繁荣后段：技术价值已经得到验证，但价格和资本开支正在提前兑现多年增长。它还不像历史顶部那样完成了全面杠杆化与普遍现金流恶化，因此结论是“偏热、需要盈利验证”，而不是“已经确定破裂”。"
    return "AI仍更接近商业扩张阶段，历史类比提示应持续观察资本开支、融资杠杆和盈利兑现，而不是仅凭技术热度断言泡沫。"
