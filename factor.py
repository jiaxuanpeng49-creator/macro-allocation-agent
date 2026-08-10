def to_signal(momentum, threshold):
    """
    把连续的动量数值转换成离散信号。

    1：上升
    0：变化不明显
    -1：下降
    """

    if momentum > threshold:
        return 1

    if momentum < -threshold:
        return -1

    return 0


def calculate_factors(data):
    """
    根据最近一期数据和前三期平均值，
    计算增长、通胀和流动性因子。
    """

    if len(data) < 4:
        raise ValueError("至少需要4期宏观数据才能计算因子")

    current = data[-1]
    previous_three = data[-4:-1]

    average_pmi = sum(
        item["PMI"] for item in previous_three
    ) / 3

    average_cpi = sum(
        item["CPI"] for item in previous_three
    ) / 3

    average_rate = sum(
        item["interest_rate"] for item in previous_three
    ) / 3

    growth_momentum = (
        current["PMI"] - average_pmi
    )

    inflation_momentum = (
        current["CPI"] - average_cpi
    )

    liquidity_momentum = (
        average_rate - current["interest_rate"]
    )

    factors = {
        "growth": to_signal(
            growth_momentum,
            threshold=0.2
        ),
        "inflation": to_signal(
            inflation_momentum,
            threshold=0.1
        ),
        "liquidity": to_signal(
            liquidity_momentum,
            threshold=0.1
        )
    }

    return factors