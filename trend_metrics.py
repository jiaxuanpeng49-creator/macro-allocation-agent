"""从每日新闻的现有规则结果提取可审计的主题趋势指标。"""

from collections import defaultdict


def derive_topic_metrics(articles):
    """按主题聚合已有文章评分，不调用模型，也不补齐不存在的数据。

    主题评分定义为文章对现有资产集合影响的等权平均，再按新闻相关度加权；
    主题资产影响则直接对同主题文章的各资产影响按相关度加权。
    """
    totals = defaultdict(float)
    weights = defaultdict(float)
    asset_totals = defaultdict(lambda: defaultdict(float))
    asset_weights = defaultdict(lambda: defaultdict(float))

    for article in articles or []:
        topic = str(article.get("category") or "").strip()
        impacts = article.get("asset_impact") or {}
        numeric_impacts = {
            str(asset): float(value)
            for asset, value in impacts.items()
            if isinstance(value, (int, float))
        }
        if not topic or not numeric_impacts:
            continue
        weight = max(1.0, float(article.get("relevance_score") or 1))
        article_score = sum(numeric_impacts.values()) / len(numeric_impacts)
        totals[topic] += article_score * weight
        weights[topic] += weight
        for asset, value in numeric_impacts.items():
            asset_totals[topic][asset] += value * weight
            asset_weights[topic][asset] += weight

    topic_scores = {
        topic: round(totals[topic] / weights[topic], 3)
        for topic in sorted(totals)
        if weights[topic]
    }
    topic_asset_impacts = {
        topic: {
            asset: round(total / asset_weights[topic][asset], 3)
            for asset, total in sorted(asset_totals[topic].items())
            if asset_weights[topic][asset]
        }
        for topic in sorted(asset_totals)
    }
    return topic_scores, topic_asset_impacts
