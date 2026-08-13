"""投资驾驶舱：今日结论、配置、依据与个人适配。"""

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ai_bubble_diagnosis import unified_ai_bubble_diagnosis
from news_intelligence import load_news_intelligence
from personal_allocation import OCCUPATION_STABILITY, run_personalized_allocation
from pipeline import run_macro_analysis
from ui_theme import render_app_header, section_header, style_plotly


NEUTRAL_PROFILE = {
    "age": 35,
    "occupation": "成熟行业雇员",
    "monthly_income": 20000.0,
    "monthly_expenses": 10000.0,
    "liquid_assets": 300000.0,
    "high_interest_debt": 0.0,
    "dependents": 0,
    "horizon_years": 10,
    "max_loss_pct": 20,
    "risk_willingness": 3,
    "investment_experience": 3,
    "income_stability": None,
    "liquidity_need": None,
}


@st.cache_data(ttl=1800, show_spinner=False)
def _decision_context():
    return run_macro_analysis(), unified_ai_bubble_diagnosis(), load_news_intelligence()


def _current_context():
    try:
        return _decision_context()
    except Exception as exc:
        st.error(f"当前环境暂时无法完整计算：{exc}")
        return None, None, None


def _news_tone(report):
    if not report:
        return "暂无快照", "等待每日情报更新"
    stock = float(report.get("asset_impact", {}).get("股票", 0))
    if stock > 0.35:
        tone = "偏多"
    elif stock < -0.35:
        tone = "偏空"
    else:
        tone = "中性"
    return tone, report.get("summary", "当日新闻尚未形成显著方向。")


def _base_allocation(current):
    weights = dict(current["portfolio_weights"])
    weights["现金"] = 0.0
    return weights


def _render_allocation(weights, title, profile_label, amount=None):
    left, right = st.columns([1, 1.35], gap="large")
    colors = ["#4266E8", "#775CF0", "#D39A55", "#B9C2DF"]
    pie = go.Figure(
        go.Pie(
            labels=list(weights),
            values=list(weights.values()),
            hole=0.62,
            textinfo="label+percent",
            sort=False,
            marker={"colors": colors, "line": {"color": "rgba(255,255,255,.94)", "width": 3}},
        )
    )
    style_plotly(pie, title, 430)
    pie.update_layout(showlegend=False, annotations=[{"text": profile_label, "showarrow": False, "font": {"size": 18}}])
    left.plotly_chart(pie, width="stretch")

    table = pd.DataFrame({"资产": list(weights), "配置比例": [f"{value:.1%}" for value in weights.values()]})
    if amount is not None:
        table["参考金额"] = [f"{amount * value:,.0f}" for value in weights.values()]
    right.dataframe(table, hide_index=True, width="stretch")
    for asset, weight, color in zip(weights, weights.values(), colors):
        right.markdown(
            f"""
            <div class="fin-allocation-line">
              <span><i style="background:{color}"></i>{asset}</span>
              <div><b style="width:{max(weight * 100, 2):.1f}%;background:{color}"></b></div>
              <strong>{weight:.1%}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_overview(current, diagnosis, news):
    personal = st.session_state.get("personal_result")
    profile = personal["profile"]["level"] if personal else "尚未个人适配"
    news_tone, _ = _news_tone(news)
    cycle = current["cycle"] if current else "等待更新"
    score = diagnosis["stage_score"] if diagnosis else 0
    description = (
        f"当前处于{cycle}环境，AI 热度为 {score}/100，新闻风向{news_tone}。"
        + (f" 已结合你的{profile}风险边界生成最终组合。" if personal else " 完善选填资料后，将生成个人约束下的最终组合。")
    )
    render_app_header(
        title="今天的配置",
        gradient_word="先守后攻",
        description=description,
        eyebrow="PERSONAL × MACRO × INTELLIGENCE",
        sphere_label="AI",
        badges=[("经济周期", cycle), ("新闻风向", news_tone), ("泡沫热度", f"{score} / 100"), ("个人边界", profile)],
    )
    c1, c2, c3 = st.columns([1, 1, 1.4])
    c1.metric("信号完整度", "4 / 4" if personal else "3 / 4")
    c2.metric("当前风险类型", profile)
    with c3:
        st.markdown(
            f"""
            <div class="fin-quiet-note">
              <span>最新综合更新时间</span>
              <strong>{datetime.now().strftime('%Y-%m-%d %H:%M')}</strong>
              <p>已合并宏观、每日新闻、AI 泡沫{('与个人情况' if personal else '')}。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_allocation(current):
    section_header("02 / ALLOCATION", "最终配置方案", "先应用个人风险边界，再允许宏观信号在边界内调整。")
    personal = st.session_state.get("personal_result")
    if personal:
        cash_flow = personal["cash_flow"]
        _render_allocation(
            personal["final_weights"],
            "个人约束 × 当前环境",
            personal["profile"]["level"],
            cash_flow["investable_assets_now"],
        )
        status_cols = st.columns(3)
        status_cols[0].metric("应急资金目标", f"{cash_flow['emergency_target']:,.0f}")
        status_cols[1].metric("当前可投资资产", f"{cash_flow['investable_assets_now']:,.0f}")
        status_cols[2].metric("每月可结余", f"{cash_flow['monthly_surplus']:,.0f}")
        if cash_flow["emergency_gap"] > 0:
            st.warning(f"距离应急资金目标还差 {cash_flow['emergency_gap']:,.0f}。{personal['priority']}。")
        else:
            st.success(personal["priority"])
    elif current:
        st.info("当前展示宏观基础组合。进入“04 个人适配”填写任意资料后，会生成个人最终组合。")
        _render_allocation(_base_allocation(current), "宏观环境基础权重", "未个人化")


def render_signals(current, diagnosis, news):
    section_header("03 / EVIDENCE", "今天为什么这样配", "三个信号处于同一决策层：周期决定方向，新闻修正短期，个人约束决定上限。")
    tone, news_summary = _news_tone(news)
    cols = st.columns(3, gap="large")
    cards = [
        ("经济周期", current["cycle"] if current else "等待更新", "通胀与增长共同决定股票、债券和黄金的基础倾向。"),
        ("新闻风向", tone, news_summary),
        ("泡沫热度", f"{diagnosis['stage_score']}/100" if diagnosis else "--", diagnosis["stage"] if diagnosis else "等待更新"),
    ]
    for col, (label, value, copy) in zip(cols, cards):
        with col.container(border=True):
            st.caption(label)
            st.markdown(f"## {value}")
            st.write(copy)
    if diagnosis:
        st.success("**统一结论：** " + diagnosis["conclusion"])
    if current:
        with st.expander("查看宏观因子与资产得分"):
            st.json({"宏观因子": current["factors"], "资产得分": current["asset_scores"]})


def _optional_profile_values():
    c1, c2, c3 = st.columns(3)
    occupation = c1.selectbox("职业", list(OCCUPATION_STABILITY), index=None, placeholder="选填")
    annual_income = c2.number_input("年收入", min_value=0.0, value=None, step=10000.0, placeholder="选填")
    income_stability = c3.selectbox("收入稳定性", ["很稳定", "较稳定", "一般", "波动较大"], index=None, placeholder="选填")
    c4, c5, c6 = st.columns(3)
    age = c4.number_input("年龄", min_value=18, max_value=90, value=None, step=1, placeholder="选填")
    dependents = c5.number_input("家庭负担人数", min_value=0, max_value=10, value=None, step=1, placeholder="选填")
    monthly_expenses = c6.number_input("每月必要支出", min_value=0.0, value=None, step=1000.0, placeholder="选填")
    c7, c8, c9 = st.columns(3)
    liquid_assets = c7.number_input("可投资及流动资产", min_value=0.0, value=None, step=10000.0, placeholder="选填")
    debt = c8.number_input("高息债务余额", min_value=0.0, value=None, step=10000.0, placeholder="选填")
    horizon = c9.selectbox("投资期限", [1, 3, 5, 8, 10, 15, 20, 30], index=None, placeholder="选填", format_func=lambda value: f"{value} 年")
    c10, c11, c12 = st.columns(3)
    max_loss = c10.selectbox("可接受最大回撤", [5, 10, 15, 20, 25, 30, 40, 50], index=None, placeholder="选填", format_func=lambda value: f"{value}%")
    willingness = c11.selectbox("主观风险意愿", [1, 2, 3, 4, 5], index=None, placeholder="选填", format_func=lambda value: f"{value} / 5")
    experience = c12.selectbox("投资经验", [1, 2, 3, 4, 5], index=None, placeholder="选填", format_func=lambda value: f"{value} / 5")
    liquidity_need = st.selectbox("未来三年流动性需求", ["低", "中", "高"], index=None, placeholder="选填")
    return {
        "age": age,
        "occupation": occupation,
        "annual_income": annual_income,
        "monthly_expenses": monthly_expenses,
        "liquid_assets": liquid_assets,
        "high_interest_debt": debt,
        "dependents": dependents,
        "horizon_years": horizon,
        "max_loss_pct": max_loss,
        "risk_willingness": willingness,
        "investment_experience": experience,
        "income_stability": income_stability,
        "liquidity_need": liquidity_need,
    }


def render_personal():
    section_header("04 / PERSONAL FIT", "配置首先服务于你", "以下资料全部选填；模型只强化你实际提供的信息，其余项目采用中性假设。")
    with st.form("optional_personal_profile", border=True):
        values = _optional_profile_values()
        submitted = st.form_submit_button("根据已填信息重新判断", type="primary", width="stretch")
    if submitted:
        supplied = {key: value for key, value in values.items() if value is not None}
        resolved = dict(NEUTRAL_PROFILE)
        for key, value in supplied.items():
            if key == "annual_income":
                resolved["monthly_income"] = value / 12
            else:
                resolved[key] = value
        result = run_personalized_allocation(
            age=resolved["age"],
            occupation=resolved["occupation"],
            monthly_income=resolved["monthly_income"],
            monthly_expenses=resolved["monthly_expenses"],
            liquid_assets=resolved["liquid_assets"],
            high_interest_debt=resolved["high_interest_debt"],
            dependents=resolved["dependents"],
            horizon_years=resolved["horizon_years"],
            max_loss_pct=resolved["max_loss_pct"],
            risk_willingness=resolved["risk_willingness"],
            investment_experience=resolved["investment_experience"],
            income_stability=resolved["income_stability"],
            liquidity_need=resolved["liquidity_need"],
        )
        st.session_state["personal_result"] = result
        st.session_state["personal_field_count"] = len(supplied)
        st.session_state["personal_fields"] = supplied

    result = st.session_state.get("personal_result")
    if result:
        count = st.session_state.get("personal_field_count", 0)
        p1, p2, p3 = st.columns(3)
        p1.metric("个人风险类型", result["profile"]["level"])
        p2.metric("风险评分", f"{result['profile']['score']}/100")
        p3.metric("采用的个人信息", f"{count} 项")
        st.success(f"已根据 {count} 项实际资料重新判断；未填写项目使用中性假设。")
        with st.expander("查看风险边界与计算说明"):
            for rule in result["guardrails"]:
                st.markdown(f"- {rule}")
            st.caption(result["disclaimer"])
    else:
        st.info("目前尚未保存个人资料，网站先展示宏观基础建议。即使只填写一项，也可以开始生成个人适配。")


def render_investment_dashboard():
    current, diagnosis, news = _current_context()
    overview_tab, allocation_tab, signals_tab, personal_tab = st.tabs(
        ["01 今日结论", "02 配置方案", "03 判断依据", "04 个人适配"],
        key="dashboard_chapters",
        on_change="rerun",
    )
    if overview_tab.open:
        with overview_tab:
            render_overview(current, diagnosis, news)
    if allocation_tab.open:
        with allocation_tab:
            render_allocation(current)
    if signals_tab.open:
        with signals_tab:
            render_signals(current, diagnosis, news)
    if personal_tab.open:
        with personal_tab:
            render_personal()
