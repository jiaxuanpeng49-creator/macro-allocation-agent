"""把个人风险承受能力与当前宏观配置建议合成为约束后的资产配置。"""

from copy import deepcopy

from ai_bubble_diagnosis import compact_diagnosis
from pipeline import run_macro_analysis

OCCUPATION_STABILITY = {
    "公务员/事业单位/稳定雇员": 5,
    "成熟行业雇员": 4,
    "科技/金融等周期行业雇员": 3,
    "自由职业/个体经营": 2,
    "创业者/收入高度波动": 1,
}

STRATEGIC_WEIGHTS = {
    "保守型": {"股票": 0.25, "债券": 0.50, "黄金": 0.10, "现金": 0.15},
    "稳健型": {"股票": 0.45, "债券": 0.38, "黄金": 0.10, "现金": 0.07},
    "成长型": {"股票": 0.65, "债券": 0.24, "黄金": 0.08, "现金": 0.03},
    "进取型": {"股票": 0.78, "债券": 0.14, "黄金": 0.05, "现金": 0.03},
}

EQUITY_CAPS = {"保守型": 0.35, "稳健型": 0.55, "成长型": 0.72, "进取型": 0.85}

INCOME_STABILITY = {"波动较大": 2, "一般": 3, "较稳定": 4, "很稳定": 5}
LIQUIDITY_CASH_ADJUSTMENT = {"低": -0.02, "中": 0.02, "高": 0.08}


def _clamp(value, low, high):
    return max(low, min(high, value))


def _risk_profile(
    age, occupation, monthly_income, monthly_expenses, liquid_assets,
    high_interest_debt, dependents, horizon_years, max_loss_pct,
    risk_willingness, investment_experience, income_stability=None,
):
    income = max(float(monthly_income), 0)
    expenses = max(float(monthly_expenses), 0)
    assets = max(float(liquid_assets), 0)
    debt = max(float(high_interest_debt), 0)
    stability = INCOME_STABILITY.get(income_stability, OCCUPATION_STABILITY[occupation])
    savings_rate = (income - expenses) / income if income else -1
    coverage = assets / expenses if expenses else 24

    ability = 0
    ability += _clamp(horizon_years / 20, 0, 1) * 25
    ability += _clamp(max_loss_pct / 35, 0, 1) * 20
    ability += stability / 5 * 15
    ability += _clamp((savings_rate + 0.05) / 0.45, 0, 1) * 15
    ability += _clamp(coverage / 12, 0, 1) * 10
    ability += (1 - _clamp(debt / max(assets, 1), 0, 1)) * 10
    ability += _clamp((65 - age) / 45, 0, 1) * 5
    ability -= min(max(dependents, 0) * 2, 8)
    willingness = _clamp((risk_willingness - 1) / 4, 0, 1) * 70 + _clamp(investment_experience / 5, 0, 1) * 30
    # 实际配置取“承受能力”和“主观意愿”中更低者，避免愿意冒险但无能力承担损失。
    total = round(_clamp(min(ability, willingness), 0, 100))
    if total <= 30:
        level = "保守型"
    elif total <= 52:
        level = "稳健型"
    elif total <= 75:
        level = "成长型"
    else:
        level = "进取型"
    return {
        "score": total,
        "level": level,
        "ability_score": round(_clamp(ability, 0, 100)),
        "willingness_score": round(willingness),
        "job_stability": stability,
        "savings_rate": savings_rate,
        "emergency_coverage_months": coverage,
    }


def _emergency_months(occupation, dependents, high_interest_debt, income_stability=None, liquidity_need=None):
    months = 6
    stability = INCOME_STABILITY.get(income_stability, OCCUPATION_STABILITY[occupation])
    if stability <= 2:
        months += 3
    elif stability == 3:
        months += 1
    months += min(max(dependents, 0), 2)
    if high_interest_debt > 0:
        months += 1
    if liquidity_need == "中":
        months += 1
    elif liquidity_need == "高":
        months += 3
    return int(_clamp(months, 3, 12))


def _normalize(weights):
    total = sum(weights.values())
    return {asset: value / total for asset, value in weights.items()}


def run_personalized_allocation(
    age=35,
    occupation="成熟行业雇员",
    monthly_income=20000,
    monthly_expenses=10000,
    liquid_assets=300000,
    high_interest_debt=0,
    dependents=0,
    horizon_years=10,
    max_loss_pct=20,
    risk_willingness=3,
    investment_experience=3,
    income_stability=None,
    liquidity_need=None,
):
    """生成“个人底线约束 + 宏观倾斜”的教育性配置建议。金额使用用户输入的同一币种。"""
    if occupation not in OCCUPATION_STABILITY:
        raise ValueError(f"occupation 必须是 {list(OCCUPATION_STABILITY)} 之一")
    profile = _risk_profile(
        age, occupation, monthly_income, monthly_expenses, liquid_assets,
        high_interest_debt, dependents, horizon_years, max_loss_pct,
        risk_willingness, investment_experience, income_stability,
    )
    emergency_months = _emergency_months(
        occupation, dependents, high_interest_debt, income_stability, liquidity_need
    )
    emergency_target = emergency_months * max(float(monthly_expenses), 0)
    emergency_gap = max(emergency_target - float(liquid_assets), 0)
    investable_now = max(float(liquid_assets) - emergency_target - float(high_interest_debt), 0)
    monthly_surplus = max(float(monthly_income) - float(monthly_expenses), 0)

    strategic = deepcopy(STRATEGIC_WEIGHTS[profile["level"]])
    if liquidity_need in LIQUIDITY_CASH_ADJUSTMENT:
        strategic["现金"] = _clamp(
            strategic["现金"] + LIQUIDITY_CASH_ADJUSTMENT[liquidity_need],
            0.03,
            0.25,
        )
    macro = run_macro_analysis()
    macro_risky = _normalize(macro["portfolio_weights"])
    cash_weight = strategic["现金"]
    base_risky = _normalize({k: strategic[k] for k in ["股票", "债券", "黄金"]})
    tilt_strength = 0.25
    risky = {
        asset: (1 - tilt_strength) * base_risky[asset] + tilt_strength * macro_risky[asset]
        for asset in base_risky
    }
    final = {asset: risky[asset] * (1 - cash_weight) for asset in risky}
    final["现金"] = cash_weight

    bubble = compact_diagnosis()
    # 高泡沫热度只限制股票上限，不直接清仓；腾出的权重按债券/黄金比例分配。
    bubble_haircut = 0.05 if bubble["stage_score"] >= 70 else 0
    equity_cap = max(EQUITY_CAPS[profile["level"]] - bubble_haircut, 0)
    if final["股票"] > equity_cap:
        excess = final["股票"] - equity_cap
        final["股票"] = equity_cap
        defensive_total = final["债券"] + final["黄金"]
        final["债券"] += excess * final["债券"] / defensive_total
        final["黄金"] += excess * final["黄金"] / defensive_total
    gold_cap = 0.15 if profile["level"] == "保守型" else 0.12
    if final["黄金"] > gold_cap:
        final["债券"] += final["黄金"] - gold_cap
        final["黄金"] = gold_cap
    final = _normalize(final)
    rounded_final = {key: round(value, 6) for key, value in final.items()}
    rounded_final["现金"] = round(rounded_final["现金"] + 1 - sum(rounded_final.values()), 6)

    priority = "可以开始按目标配置投资"
    if emergency_gap > 0:
        priority = "先补足应急资金，再逐步投资"
    if high_interest_debt > 0:
        priority = "优先评估并偿还高息债务，同时保留基本应急金"

    return {
        "profile": profile,
        "cash_flow": {
            "monthly_surplus": monthly_surplus,
            "emergency_months": emergency_months,
            "emergency_target": emergency_target,
            "emergency_gap": emergency_gap,
            "investable_assets_now": investable_now,
        },
        "strategic_weights": strategic,
        "macro_environment": {
            "as_of_date": macro["as_of_date"],
            "cycle": macro["cycle"],
            "macro_weights": macro["portfolio_weights"],
            "ai_bubble_stage": bubble["stage"],
            "ai_bubble_score": bubble["stage_score"],
            "income_stability": income_stability,
            "liquidity_need": liquidity_need,
        },
        "final_weights": rounded_final,
        "monthly_contribution": {
            asset: round(monthly_surplus * weight, 2) for asset, weight in final.items()
        },
        "priority": priority,
        "method": "个人战略配置占75%，当前宏观模型占25%；收入稳定性影响风险承受能力，流动性需求影响应急资金与现金权重；AI泡沫热度达到70时，个人风险等级的股票上限下调5个百分点。",
        "guardrails": [
            "应急资金与近期必用资金不进入风险资产",
            "实际风险等级取承受能力和主观意愿中较低者",
            "宏观信号只能在个人风险上限内倾斜，不能突破上限",
            "至少每年或个人收入、家庭责任、目标发生变化时重新评估",
        ],
        "disclaimer": "这是教育性规则模型，不构成针对证券、基金或税务的个性化投资建议。",
    }
