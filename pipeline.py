from macro_data import get_macro_data
from factor import calculate_factors
from cycle import judge_cycle
from asset_score import calculate_asset_scores
from portfolio import scores_to_weights


def run_macro_analysis():
    """
    运行完整的宏观资产配置流程。

    流程：
    1. 获取宏观数据
    2. 计算宏观因子
    3. 判断经济周期
    4. 计算资产得分
    5. 生成组合权重
    """

    data = get_macro_data()

    if not data:
        raise ValueError("没有可用的宏观数据")

    factors = calculate_factors(data)

    cycle = judge_cycle(factors)

    score_result = calculate_asset_scores(factors)

    scores = score_result["scores"]
    breakdown = score_result["breakdown"]

    weights = scores_to_weights(
        scores,
        temperature=3.0
    )

    result = {
        "as_of_date": data[-1]["date"],
        "latest_data": data[-1],
        "factors": factors,
        "cycle": cycle,
        "asset_scores": scores,
        "score_breakdown": breakdown,
        "portfolio_weights": weights
    }

    return result