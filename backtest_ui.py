"""30年历史验证页面。"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest import BENCHMARK_NAMES, run_historical_backtest
from ui_theme import section_header, style_plotly


def render_backtest_page():
    section_header(
        "30Y / BACKTEST",
        "让策略回到过去",
        "检验收益、回撤和跨周期稳定性；比较对象均为规则基准，并非机构真实历史持仓。",
    )
    control1, control2, control3 = st.columns(3)
    benchmark = control1.selectbox(
        "比较基准",
        options=list(BENCHMARK_NAMES),
        format_func=BENCHMARK_NAMES.get,
        index=1,
        key="research_benchmark",
    )
    cost_bps = control2.select_slider(
        "Agent 交易成本（bp）",
        options=[0, 5, 10, 15, 25, 50],
        value=10,
        key="research_cost",
    )
    temperature = control3.slider(
        "配置均衡度",
        min_value=1.0,
        max_value=6.0,
        value=3.0,
        step=0.5,
        key="research_temperature",
    )
    result = run_historical_backtest(cost_bps, benchmark, temperature)
    monthly = result["monthly"].copy()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Agent 年化收益", f"{result['agent']['cagr']:.2%}")
    m2.metric(
        result["benchmark"],
        f"{result['benchmark_metrics']['cagr']:.2%}",
        delta=f"{result['agent']['cagr'] - result['benchmark_metrics']['cagr']:.2%}",
    )
    m3.metric("Agent 最大回撤", f"{result['agent']['max_drawdown']:.2%}")
    m4.metric("初始100的期末财富", f"{result['agent']['ending_wealth']:.0f}")

    wealth = go.Figure()
    wealth.add_trace(go.Scatter(x=monthly.date, y=monthly.agent_wealth, name="Agent", line={"width": 3}))
    wealth.add_trace(go.Scatter(x=monthly.date, y=monthly.benchmark_wealth, name=result["benchmark"]))
    style_plotly(wealth, "累计财富（初始值100，对数坐标）", 440)
    wealth.update_layout(
        yaxis_type="log",
        hovermode="x unified",
        xaxis_title="时间",
        yaxis_title="累计财富",
        legend_title="策略",
    )
    st.plotly_chart(wealth, width="stretch")

    allocation = go.Figure()
    for field, name in [("weight_stock", "股票"), ("weight_bond", "债券"), ("weight_gold", "黄金")]:
        allocation.add_trace(
            go.Scatter(x=monthly.date, y=monthly[field], name=name, stackgroup="one", groupnorm="percent")
        )
    style_plotly(allocation, "Agent 历史配置建议", 400)
    allocation.update_layout(
        hovermode="x unified",
        xaxis_title="时间",
        yaxis_title="组合权重",
        yaxis_ticksuffix="%",
    )
    st.plotly_chart(allocation, width="stretch")

    selected_date = st.select_slider(
        "查看某个月的 Agent 判断",
        options=list(monthly.date.dt.strftime("%Y-%m")),
        value=monthly.date.iloc[-1].strftime("%Y-%m"),
        key="research_month",
    )
    row = monthly.loc[monthly.date.dt.strftime("%Y-%m") == selected_date].iloc[0]
    st.info(
        f"{selected_date}｜周期：{row.cycle}｜股票 {row.weight_stock:.1%}｜"
        f"债券 {row.weight_bond:.1%}｜黄金 {row.weight_gold:.1%}"
    )
    with st.expander("数据来源与重要局限"):
        st.markdown(
            """
            - 股票为标普500价格收益，不含股息。
            - 黄金为长期月度现货价格。
            - 债券为10年期国债收益率构造的久期代理，不是基金或正式总回报指数。
            - 宏观数据使用修订后终值而非历史 vintage，存在前视偏差风险。
            - 比较对象均为规则基准，不代表现实机构当年的真实持仓。
            """
        )

