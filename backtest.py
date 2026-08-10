"""宏观配置 Agent 的无未来函数历史回测。"""

from pathlib import Path
import math

import numpy as np
import pandas as pd

from asset_score import calculate_asset_scores
from portfolio import scores_to_weights

DATA = Path(__file__).parent / "data"
ASSETS = ["stock", "bond", "gold"]
BENCHMARK_NAMES = {
    "sixty_forty": "60/40股债",
    "equal_weight": "股债金各1/3",
    "stock": "纯股票",
}


def _month_end(index):
    dates = pd.to_datetime(index)
    if isinstance(dates, pd.Series):
        return dates.dt.to_period("M").dt.to_timestamp("M")
    return dates.to_period("M").to_timestamp("M")


def _signal(values, threshold):
    return pd.Series(
        np.where(values > threshold, 1, np.where(values < -threshold, -1, 0)),
        index=values.index,
        dtype=int,
    )


def _load_data():
    macro = pd.read_csv(DATA / "macro.csv", parse_dates=["DATE"]).set_index("DATE")
    macro.index = _month_end(macro.index)

    ip = pd.read_csv(DATA / "industrial_production.csv", parse_dates=["observation_date"])
    ip = ip.set_index("observation_date")["INDPRO"].rename("IP")
    ip.index = _month_end(ip.index)
    macro = macro.join(ip).sort_index()
    macro[["CPI", "RATE"]] = macro[["CPI", "RATE"]].interpolate(limit=2)

    market = pd.read_csv(DATA / "market.csv", parse_dates=["Date"]).set_index("Date")
    market.index = _month_end(market.index)

    gold = pd.read_csv(DATA / "gold_monthly.csv")
    gold["Date"] = _month_end(gold["Date"])
    gold_return = gold.set_index("Date")["Price"].pct_change().rename("gold")

    # 透明的10年期国债收益代理：上月票息/12 - 7年久期×收益率变化。
    y = macro["RATE"] / 100
    bond_return = (y.shift(1) / 12 - 7.0 * (y - y.shift(1))).rename("bond")
    returns = pd.concat([market["stock"], bond_return, gold_return], axis=1)
    returns = returns.loc["1995-01-31":"2025-12-31"].dropna()
    return macro, returns


def _factors(macro):
    growth_rate = macro["IP"].pct_change(12) * 100
    inflation_rate = macro["CPI"].pct_change(12) * 100
    growth_momentum = growth_rate - growth_rate.shift(1).rolling(3).mean()
    inflation_momentum = inflation_rate - inflation_rate.shift(1).rolling(3).mean()
    liquidity_momentum = macro["RATE"].shift(1).rolling(3).mean() - macro["RATE"]
    result = pd.DataFrame(index=macro.index)
    result["growth"] = _signal(growth_momentum, 0.2)
    result["inflation"] = _signal(inflation_momentum, 0.1)
    result["liquidity"] = _signal(liquidity_momentum, 0.1)
    cycle = {(1, -1): "复苏", (1, 1): "过热", (-1, 1): "滞胀", (-1, -1): "衰退"}
    result["cycle"] = [cycle.get((g, i), "中性") for g, i in zip(result.growth, result.inflation)]
    return result


def _weights(factors, temperature):
    rows = []
    for _, row in factors.iterrows():
        scores = calculate_asset_scores({
            "growth": int(row.growth),
            "inflation": int(row.inflation),
            "liquidity": int(row.liquidity),
        })["scores"]
        chinese = scores_to_weights(scores, temperature=temperature)
        rows.append({"stock": chinese["股票"], "bond": chinese["债券"], "gold": chinese["黄金"]})
    return pd.DataFrame(rows, index=factors.index)


def _metrics(returns):
    years = len(returns) / 12
    wealth = (1 + returns).cumprod()
    drawdown = wealth / wealth.cummax() - 1
    cagr = wealth.iloc[-1] ** (1 / years) - 1
    volatility = returns.std() * math.sqrt(12)
    return {
        "months": int(len(returns)),
        "cagr": float(cagr),
        "volatility": float(volatility),
        "sharpe_0rf": float(cagr / volatility),
        "max_drawdown": float(drawdown.min()),
        "ending_wealth": float(100 * wealth.iloc[-1]),
    }


def run_historical_backtest(cost_bps=10, benchmark="equal_weight", temperature=3.0):
    """返回 Agent 与规则基准的1995–2025年月度回测结果。"""
    if benchmark not in BENCHMARK_NAMES:
        raise ValueError(f"benchmark 必须是 {list(BENCHMARK_NAMES)} 之一")
    if cost_bps < 0:
        raise ValueError("cost_bps 不能小于0")

    macro, returns = _load_data()
    factors = _factors(macro).reindex(returns.index)
    # 月末生成建议，下一个月才执行，避免使用未来信息。
    weights = _weights(factors, temperature).shift(1).dropna()
    returns = returns.reindex(weights.index)
    turnover = weights.diff().abs().sum(axis=1).fillna(0) / 2
    agent_return = (weights * returns).sum(axis=1) - turnover * cost_bps / 10000

    benchmarks = pd.DataFrame(index=returns.index)
    benchmarks["sixty_forty"] = 0.6 * returns.stock + 0.4 * returns.bond
    benchmarks["equal_weight"] = returns.mean(axis=1)
    benchmarks["stock"] = returns.stock
    benchmark_return = benchmarks[benchmark]

    detail = factors.join(weights.add_prefix("weight_"))
    detail = detail.join(agent_return.rename("agent_return"))
    detail = detail.join(benchmark_return.rename("benchmark_return"))
    detail["agent_wealth"] = 100 * (1 + detail.agent_return).cumprod()
    detail["benchmark_wealth"] = 100 * (1 + detail.benchmark_return).cumprod()
    detail.index.name = "date"

    return {
        "period": f"{detail.index.min():%Y-%m} 至 {detail.index.max():%Y-%m}",
        "benchmark": BENCHMARK_NAMES[benchmark],
        "cost_bps": float(cost_bps),
        "temperature": float(temperature),
        "agent": _metrics(agent_return),
        "benchmark_metrics": _metrics(benchmark_return),
        "annual_turnover": float(turnover.mean() * 12),
        "latest_decision": {
            "date": f"{detail.index[-1]:%Y-%m}",
            "cycle": detail.iloc[-1].cycle,
            "stock": float(detail.iloc[-1].weight_stock),
            "bond": float(detail.iloc[-1].weight_bond),
            "gold": float(detail.iloc[-1].weight_gold),
        },
        "monthly": detail.reset_index(),
        "method_note": "基准均为同一资产收益构造的规则组合，不是现实机构历史持仓。",
    }


def backtest_summary(cost_bps=10, benchmark="equal_weight", temperature=3.0):
    """提供给语言模型工具调用的紧凑结果，不返回整张月度表。"""
    result = run_historical_backtest(cost_bps, benchmark, temperature)
    return {key: value for key, value in result.items() if key != "monthly"}
