import math


def scores_to_weights(scores, temperature=3.0):
    """
    使用 Softmax 把资产得分转换为组合权重。

    temperature 越小，组合越集中；
    temperature 越大，组合越均衡。
    """

    if not scores:
        raise ValueError("资产得分不能为空")

    if temperature <= 0:
        raise ValueError("temperature 必须大于0")

    maximum_score = max(scores.values())

    exponential_scores = {}

    for asset, score in scores.items():
        exponential_scores[asset] = math.exp(
            (score - maximum_score) / temperature
        )

    total = sum(exponential_scores.values())

    weights = {}

    for asset, value in exponential_scores.items():
        weights[asset] = value / total

    return weights