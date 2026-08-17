"""30年历史验证页面。"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest import BENCHMARK_NAMES, run_custom_strategy_backtest, run_historical_backtest
from strategy_interpreter import interpret_investment_idea
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

    st.divider()
    st.markdown("### 用自然语言回测你的投资逻辑")
    st.caption(
        "先由 DeepSeek 把投资思想翻译成复苏、过热、滞胀、衰退和中性五种环境下的股债金权重，"
        "再由 Python 使用同一套 1995—2025 历史数据计算结果。模型不会直接编造收益率。"
    )
    with st.form("custom_strategy_backtest_form", border=True):
        investment_idea = st.text_area(
            "描述你的配置思想和调整逻辑",
            placeholder=(
                "例如：我重视控制回撤。经济衰退时提高债券和黄金；复苏时提高股票；"
                "滞胀时主要持有黄金，并始终保持分散，不使用杠杆。"
            ),
            height=150,
            key="custom_strategy_idea",
        )
        custom_cost, custom_benchmark = st.columns(2)
        custom_cost_bps = custom_cost.select_slider(
            "自定义策略交易成本（bp）",
            options=[0, 5, 10, 15, 25, 50],
            value=10,
            key="custom_strategy_cost",
        )
        custom_benchmark_key = custom_benchmark.selectbox(
            "自定义策略比较基准",
            options=list(BENCHMARK_NAMES),
            format_func=BENCHMARK_NAMES.get,
            index=1,
            key="custom_strategy_benchmark",
        )
        submitted = st.form_submit_button("解释投资逻辑并生成历史回测", type="primary", width="stretch")
    if submitted:
        try:
            with st.spinner("DeepSeek 正在把自然语言转换成可审计配置规则，随后运行30年回测……"):
                strategy_spec = interpret_investment_idea(investment_idea)
                custom_result = run_custom_strategy_backtest(
                    strategy_spec,
                    cost_bps=custom_cost_bps,
                    benchmark=custom_benchmark_key,
                )
            st.session_state["custom_backtest_result"] = custom_result
            st.success("投资逻辑已转换为配置规则，历史回测计算完成。")
        except Exception as exc:
            st.session_state.pop("custom_backtest_result", None)
            st.error(f"暂时无法生成自定义回测：{exc}")

    custom_result = st.session_state.get("custom_backtest_result")
    if not custom_result:
        st.info("输入投资逻辑后，这里会展示模型理解、五种周期配置和确定性历史回测结果。")
        return
    spec = custom_result["strategy_spec"]
    with st.container(border=True):
        st.markdown(f"#### {spec['name']}")
        st.write(spec["summary"])
        if spec.get("assumptions"):
            st.caption("模型补充假设：" + "；".join(spec["assumptions"]))
    allocation_rows = []
    for cycle, weights in spec["cycle_weights"].items():
        allocation_rows.append(
            {
                "经济周期": cycle,
                "股票": weights["stock"],
                "债券": weights["bond"],
                "黄金": weights["gold"],
            }
        )
    st.dataframe(
        pd.DataFrame(allocation_rows).style.format({"股票": "{:.1%}", "债券": "{:.1%}", "黄金": "{:.1%}"}),
        hide_index=True,
        width="stretch",
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("自定义策略年化收益", f"{custom_result['strategy']['cagr']:.2%}")
    c2.metric("最大回撤", f"{custom_result['strategy']['max_drawdown']:.2%}")
    c3.metric("年化波动", f"{custom_result['strategy']['volatility']:.2%}")
    c4.metric("期末财富", f"{custom_result['strategy']['ending_wealth']:.0f}")
    custom_monthly = custom_result["monthly"]
    custom_chart = go.Figure()
    custom_chart.add_trace(
        go.Scatter(x=custom_monthly.date, y=custom_monthly.strategy_wealth, name=spec["name"], line={"width": 3})
    )
    custom_chart.add_trace(
        go.Scatter(x=custom_monthly.date, y=custom_monthly.benchmark_wealth, name=custom_result["benchmark"])
    )
    style_plotly(custom_chart, "你的投资逻辑｜历史财富曲线", 420)
    custom_chart.update_layout(
        yaxis_type="log",
        hovermode="x unified",
        xaxis_title="时间",
        yaxis_title="累计财富（初始100）",
    )
    st.plotly_chart(custom_chart, width="stretch")
    st.caption(custom_result["method_note"] + " 研究与教学用途，不构成投资建议。")
