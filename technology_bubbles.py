"""历史技术泡沫的可审计锚点、插值序列与生命周期比较。"""

from pathlib import Path
import json

import pandas as pd


ANALOGS_FILE = Path(__file__).parent / "knowledge" / "technology_bubble_analogs.json"
PRICE_SERIES_FILE = Path(__file__).parent / "data" / "technology_bubble_prices.csv"


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


def load_normalized_price_series(path=PRICE_SERIES_FILE):
    """读取经确认的历史代理价格并把各自 T0 归一化为100。

    CSV 必须包含 bubble_id,date,price,proxy_asset,t0_date；没有数据时返回空表，
    不使用热度锚点或插值曲线冒充资产价格。
    """
    columns = [
        "bubble_id", "date", "price", "proxy_asset", "t0_date", "source_url",
        "normalized_price", "relative_year",
    ]
    if not Path(path).exists():
        return pd.DataFrame(columns=columns), {}
    raw = pd.read_csv(path)
    required = {"bubble_id", "date", "price", "proxy_asset", "t0_date"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"历史泡沫价格文件缺少字段：{sorted(missing)}")
    raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
    raw["t0_date"] = pd.to_datetime(raw["t0_date"], errors="coerce")
    raw["price"] = pd.to_numeric(raw["price"], errors="coerce")
    raw = raw.dropna(subset=["bubble_id", "date", "t0_date", "price"])
    raw = raw.loc[raw.price > 0].sort_values(["bubble_id", "date"])
    frames = []
    errors = {}
    for bubble_id, frame in raw.groupby("bubble_id"):
        t0_dates = frame.t0_date.drop_duplicates()
        proxies = frame.proxy_asset.dropna().astype(str).str.strip().replace("", pd.NA).dropna().unique()
        if len(t0_dates) != 1 or len(proxies) != 1:
            errors[bubble_id] = "proxy_asset 或 t0_date 定义不唯一"
            continue
        t0 = t0_dates.iloc[0]
        t0_rows = frame.loc[frame.date == t0]
        if t0_rows.empty:
            errors[bubble_id] = "价格序列中不存在 T0 当日价格"
            continue
        t0_price = float(t0_rows.iloc[0].price)
        normalized = frame.copy()
        normalized["normalized_price"] = normalized.price / t0_price * 100
        normalized["relative_year"] = (normalized.date - t0).dt.days / 365.2425
        normalized["proxy_asset"] = proxies[0]
        if "source_url" not in normalized:
            normalized["source_url"] = None
        frames.append(normalized[columns])
    return (pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)), errors


def price_series_availability(price_frame=None):
    """列出每个技术周期是否具备可画图的真实代理价格。"""
    payload = load_technology_bubbles()
    price_frame = price_frame if price_frame is not None else load_normalized_price_series()[0]
    rows = []
    for bubble in payload["bubbles"]:
        frame = price_frame.loc[price_frame.bubble_id == bubble["id"]] if not price_frame.empty else price_frame
        rows.append(
            {
                "技术周期": bubble["name"],
                "资本加速年（现有热度模型）": bubble["capital_acceleration_year"],
                "资产代理": frame.proxy_asset.iloc[0] if not frame.empty else "尚未定义",
                "真实价格点数": int(len(frame)),
                "状态": "可用" if not frame.empty else "缺少已确认 proxy asset / price series",
            }
        )
    return pd.DataFrame(rows)


def get_bubble(bubble_id):
    payload = load_technology_bubbles()
    return next(item for item in payload["bubbles"] if item["id"] == bubble_id)


def ai_historical_conclusion(current_score=76):
    if current_score >= 84:
        return "AI已进入与铁路1845年、互联网2000年更接近的狂热顶部区，重点不再是追逐叙事，而是防范融资反转和估值压缩。"
    if current_score >= 62:
        return "AI更接近铁路1843年前后与互联网1997—1999年的资本繁荣后段：技术价值已经得到验证，但价格和资本开支正在提前兑现多年增长。它还不像历史顶部那样完成了全面杠杆化与普遍现金流恶化，因此结论是“偏热、需要盈利验证”，而不是“已经确定破裂”。"
    return "AI仍更接近商业扩张阶段，历史类比提示应持续观察资本开支、融资杠杆和盈利兑现，而不是仅凭技术热度断言泡沫。"
