FACTOR_ASSET_MATRIX = {
    "growth": {
        "股票": 2,
        "债券": -1,
        "黄金": 0
    },

    "inflation": {
        "股票": -1,
        "债券": -2,
        "黄金": 2
    },

    "liquidity": {
        "股票": 1,
        "债券": 2,
        "黄金": 1
    }
}


def calculate_asset_scores(factors):
    """
    根据宏观因子计算资产综合得分。

    返回：
    scores：每种资产的总分
    breakdown：每个因子对资产分数的贡献
    """

    assets = ["股票", "债券", "黄金"]

    scores = {
        asset: 0
        for asset in assets
    }

    breakdown = {
        asset: {}
        for asset in assets
    }

    for factor_name, factor_signal in factors.items():

        if factor_name not in FACTOR_ASSET_MATRIX:
            raise ValueError(
                f"未知的宏观因子：{factor_name}"
            )

        asset_impacts = FACTOR_ASSET_MATRIX[factor_name]

        for asset in assets:
            contribution = (
                factor_signal
                * asset_impacts[asset]
            )

            scores[asset] += contribution

            breakdown[asset][factor_name] = contribution

    return {
        "scores": scores,
        "breakdown": breakdown
    }