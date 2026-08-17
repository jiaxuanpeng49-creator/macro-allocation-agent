"""刷新已确认的技术泡沫代理资产价格。

只下载明确配置的宽基/行业指数，并保留月末观察值与精确 T0 观察值。
铁路、电报和电力尚无已确认且可公开复现的代理指数，因此不会写入占位数据。
"""

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "technology_bubble_prices.csv"

SERIES = (
    {
        "bubble_id": "internet_telecom",
        "series_id": "NASDAQCOM",
        "proxy_asset": "NASDAQ Composite（互联网与电信资本市场代理）",
        "t0_date": "1995-01-03",
        "end_date": "2008-12-31",
        "source_url": "https://fred.stlouisfed.org/series/NASDAQCOM",
    },
    {
        "bubble_id": "ai",
        "series_id": "NASDAQSOX",
        "proxy_asset": "PHLX Semiconductor Index（AI算力资本市场代理）",
        "t0_date": "2012-01-03",
        "end_date": None,
        "source_url": "https://fred.stlouisfed.org/series/NASDAQSOX",
    },
    {
        "bubble_id": "biotech_genomics",
        "series_id": "NASDAQNBI",
        "proxy_asset": "NASDAQ Biotechnology Index（生物科技资本市场代理）",
        "t0_date": "2010-01-04",
        "end_date": "2018-12-31",
        "source_url": "https://fred.stlouisfed.org/series/NASDAQNBI",
    },
    {
        "bubble_id": "clean_energy",
        "series_id": "NASDAQCELS",
        "proxy_asset": "NASDAQ Clean Edge Green Energy Index（清洁能源代理）",
        "t0_date": "2019-01-02",
        "end_date": "2024-12-31",
        "source_url": "https://fred.stlouisfed.org/series/NASDAQCELS",
    },
    {
        "bubble_id": "mobile_cloud",
        "series_id": "NASDAQNDXT",
        "proxy_asset": "NASDAQ-100 Technology Sector（移动互联网与云计算代理）",
        "t0_date": "2009-01-02",
        "end_date": "2023-12-31",
        "source_url": "https://fred.stlouisfed.org/series/NASDAQNDXT",
    },
)


def _download_series(config):
    series_id = config["series_id"]
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    frame = pd.read_csv(url)
    frame.columns = ["date", "price"]
    frame["date"] = pd.to_datetime(frame.date, errors="coerce")
    frame["price"] = pd.to_numeric(frame.price, errors="coerce")
    frame = frame.dropna().sort_values("date")
    start = pd.Timestamp(config["t0_date"])
    frame = frame.loc[frame.date >= start]
    if config["end_date"]:
        frame = frame.loc[frame.date <= pd.Timestamp(config["end_date"])]
    t0 = frame.loc[frame.date == start]
    if t0.empty:
        raise ValueError(f"{series_id} 缺少配置的 T0 观察值 {start:%Y-%m-%d}")

    monthly = frame.groupby(frame.date.dt.to_period("M"), sort=True).tail(1)
    frame = pd.concat([t0, monthly], ignore_index=True).drop_duplicates("date")
    frame = frame.sort_values("date")
    frame.insert(0, "bubble_id", config["bubble_id"])
    frame["proxy_asset"] = config["proxy_asset"]
    frame["t0_date"] = config["t0_date"]
    frame["source_url"] = config["source_url"]
    return frame


def main():
    frames = [_download_series(config) for config in SERIES]
    output = pd.concat(frames, ignore_index=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT, index=False, date_format="%Y-%m-%d")
    for config in SERIES:
        count = int((output.bubble_id == config["bubble_id"]).sum())
        print(f"{config['bubble_id']}：保存 {count} 个真实价格观察值")
    print(f"已写入：{OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"价格数据刷新失败：{exc}", file=sys.stderr)
        raise
