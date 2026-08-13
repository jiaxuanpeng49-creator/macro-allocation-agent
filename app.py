"""宏观资产配置 Agent 的 Streamlit 图形界面。"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest import BENCHMARK_NAMES, run_historical_backtest
from bubble_ui import render_ai_bubble_page
from news_ui import render_news_intelligence_page
from personal_allocation import OCCUPATION_STABILITY, run_personalized_allocation
from pipeline import run_macro_analysis
from ui_theme import apply_theme, render_app_header, render_brand_bar, section_header, style_plotly

st.set_page_config(page_title="宏观资产配置 Agent", layout="wide", initial_sidebar_state="collapsed")
apply_theme()
render_brand_bar()

combined_tab, history_tab, knowledge_tab, news_tab, chat_tab = st.tabs(
    ["综合配置建议", "30年历史回测", "AI泡沫知识库", "每日新闻情报", "与 Agent 对话"]
)

with combined_tab:
    render_app_header()
    with st.container(border=True):
        section_header("01 / ENVIRONMENT", "识别当前大环境", "宏观模型的原始权重只作为环境信号，不是最终给个人的配置建议。")
        try:
            current = run_macro_analysis()
            st.markdown(f"#### {current['as_of_date']}｜当前周期：{current['cycle']}")
            cols = st.columns(3)
            for col, asset in zip(cols, ["股票", "债券", "黄金"]):
                col.metric(f"宏观模型偏好·{asset}", f"{current['portfolio_weights'][asset]:.1%}")
            with st.expander("查看宏观因子与资产得分"):
                st.json({"宏观因子": current["factors"], "资产得分": current["asset_scores"]})
        except Exception as exc:
            st.error(f"当前建议暂时无法计算：{exc}")

with combined_tab:
    with st.container(border=True):
        section_header(
            "02 / PERSONALIZATION",
            "加入个人情况，生成唯一的最终建议",
            "先保护应急资金和个人风险底线，再允许宏观信号在边界内调整。金额可使用人民币或其他同一币种。",
        )
        with st.form("personal_profile"):
            c1, c2, c3 = st.columns(3)
            age = c1.number_input("年龄", min_value=18, max_value=90, value=35)
            occupation = c2.selectbox("职业与收入稳定性", list(OCCUPATION_STABILITY), index=1)
            dependents = c3.number_input("需要负担的人数", min_value=0, max_value=10, value=0)
            c4, c5, c6 = st.columns(3)
            monthly_income = c4.number_input("每月税后收入", min_value=0.0, value=20000.0, step=1000.0)
            monthly_expenses = c5.number_input("每月必要支出", min_value=0.0, value=10000.0, step=1000.0)
            liquid_assets = c6.number_input("现有流动资产", min_value=0.0, value=300000.0, step=10000.0)
            c7, c8, c9 = st.columns(3)
            high_interest_debt = c7.number_input("高息债务余额", min_value=0.0, value=0.0, step=10000.0)
            horizon_years = c8.slider("投资期限（年）", 1, 30, 10)
            max_loss_pct = c9.slider("一年内最多能接受的账面损失", 5, 50, 20, format="%d%%")
            c10, c11 = st.columns(2)
            risk_willingness = c10.slider("主观风险意愿（1低—5高）", 1, 5, 3)
            investment_experience = c11.slider("投资经验（1少—5丰富）", 1, 5, 3)
            submitted = st.form_submit_button("生成个人 × 宏观综合配置", type="primary", width="stretch")

    if submitted:
        personal = run_personalized_allocation(
            age=age, occupation=occupation, monthly_income=monthly_income,
            monthly_expenses=monthly_expenses, liquid_assets=liquid_assets,
            high_interest_debt=high_interest_debt, dependents=dependents,
            horizon_years=horizon_years, max_loss_pct=max_loss_pct,
            risk_willingness=risk_willingness,
            investment_experience=investment_experience,
        )
        profile = personal["profile"]
        cash_flow = personal["cash_flow"]
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("个人风险类型", profile["level"])
        p2.metric("风险评分", f"{profile['score']}/100")
        p3.metric("应急资金目标", f"{cash_flow['emergency_target']:,.0f}", f"{cash_flow['emergency_months']}个月支出")
        p4.metric("当前可投资资产", f"{cash_flow['investable_assets_now']:,.0f}")
        if cash_flow["emergency_gap"] > 0:
            st.warning(f"距离应急资金目标还差 {cash_flow['emergency_gap']:,.0f}。{personal['priority']}。")
        else:
            st.success(personal["priority"])

        allocation_col, explanation_col = st.columns([3, 2])
        weights = personal["final_weights"]
        pie = go.Figure(go.Pie(
            labels=list(weights), values=list(weights.values()), hole=0.45,
            textinfo="label+percent", sort=False,
            marker={"line": {"color": "rgba(255,255,255,.92)", "width": 3}},
        ))
        style_plotly(pie, "个人约束 × 当前大环境后的最终配置", 410)
        pie.update_layout(showlegend=False)
        allocation_col.plotly_chart(pie, width="stretch")
        allocation_col.dataframe(
            pd.DataFrame({
                "资产": list(weights),
                "配置比例": [f"{value:.1%}" for value in weights.values()],
                "当前可配置金额": [
                    f"{cash_flow['investable_assets_now'] * value:,.0f}" for value in weights.values()
                ],
            }),
            hide_index=True,
            width="stretch",
        )
        explanation_col.markdown("#### 配置依据")
        explanation_col.write(
            f"当前宏观周期：**{personal['macro_environment']['cycle']}**  "
            f"\nAI泡沫阶段：**{personal['macro_environment']['ai_bubble_stage']}**  "
            f"\n模型方法：{personal['method']}"
        )
        explanation_col.markdown("#### 每月结余的建议分配")
        for asset, amount in personal["monthly_contribution"].items():
            explanation_col.write(f"{asset}：{amount:,.0f}")

        with st.expander("为什么是这个风险等级与配置"):
            st.write(
                f"客观承受能力 {profile['ability_score']}/100；主观风险意愿与经验 "
                f"{profile['willingness_score']}/100；模型取两者中较低者。"
            )
            st.write(f"储蓄率：{profile['savings_rate']:.1%}；现有资金可覆盖必要支出：{profile['emergency_coverage_months']:.1f}个月。")
            for rule in personal["guardrails"]:
                st.markdown(f"- {rule}")
            st.caption(personal["disclaimer"])

with history_tab:
    render_app_header(
        title="历史验证",
        gradient_word="Backtest",
        description="让策略回到过去三十年，检验收益、风险和跨周期稳定性，而不是只展示一个漂亮的终点数字。",
        eyebrow="THIRTY YEARS × EIGHT CYCLES",
        sphere_label="30Y",
        badges=[("历史区间", "1995–2025"), ("频率", "月度"), ("基准", "可切换"), ("成本", "可调节")],
    )
    section_header("BACKTEST / 30Y", "30年历史回测", "检验 Agent 规则在多个经济周期中的收益、回撤与动态配置。")
    control1, control2, control3 = st.columns(3)
    benchmark = control1.selectbox(
        "比较基准",
        options=list(BENCHMARK_NAMES),
        format_func=BENCHMARK_NAMES.get,
        index=1,
    )
    cost_bps = control2.select_slider("Agent 交易成本（bp）", options=[0, 5, 10, 15, 25, 50], value=10)
    temperature = control3.slider("配置均衡度", min_value=1.0, max_value=6.0, value=3.0, step=0.5)
    result = run_historical_backtest(cost_bps, benchmark, temperature)
    monthly = result["monthly"].copy()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Agent 年化收益", f"{result['agent']['cagr']:.2%}")
    m2.metric(result["benchmark"], f"{result['benchmark_metrics']['cagr']:.2%}",
              delta=f"{result['agent']['cagr'] - result['benchmark_metrics']['cagr']:.2%}")
    m3.metric("Agent 最大回撤", f"{result['agent']['max_drawdown']:.2%}")
    m4.metric("初始100的期末财富", f"{result['agent']['ending_wealth']:.0f}")

    wealth = go.Figure()
    wealth.add_trace(go.Scatter(x=monthly.date, y=monthly.agent_wealth, name="Agent", line={"width": 3}))
    wealth.add_trace(go.Scatter(x=monthly.date, y=monthly.benchmark_wealth, name=result["benchmark"]))
    style_plotly(wealth, "累计财富（初始值100，对数坐标）", 440)
    wealth.update_layout(yaxis_type="log", hovermode="x unified",
                         xaxis_title="时间", yaxis_title="累计财富", legend_title="策略")
    st.plotly_chart(wealth, width="stretch")

    allocation = go.Figure()
    for field, name in [("weight_stock", "股票"), ("weight_bond", "债券"), ("weight_gold", "黄金")]:
        allocation.add_trace(go.Scatter(x=monthly.date, y=monthly[field], name=name,
                                        stackgroup="one", groupnorm="percent"))
    style_plotly(allocation, "Agent 历史配置建议", 400)
    allocation.update_layout(hovermode="x unified", xaxis_title="时间",
                             yaxis_title="组合权重", yaxis_ticksuffix="%")
    st.plotly_chart(allocation, width="stretch")

    selected_date = st.select_slider(
        "查看某个月的 Agent 判断",
        options=list(monthly.date.dt.strftime("%Y-%m")),
        value=monthly.date.iloc[-1].strftime("%Y-%m"),
    )
    row = monthly.loc[monthly.date.dt.strftime("%Y-%m") == selected_date].iloc[0]
    st.info(
        f"{selected_date}｜周期：{row.cycle}｜股票 {row.weight_stock:.1%}｜"
        f"债券 {row.weight_bond:.1%}｜黄金 {row.weight_gold:.1%}"
    )
    with st.expander("数据来源与重要局限"):
        st.markdown(
            """
            - 股票：原项目 Yahoo Finance 标普500价格收益，不含股息。
            - 黄金：长期月度现货价格。
            - 债券：10年期国债收益率构造的久期代理，不是基金或正式总回报指数。
            - 宏观数据：工业产出、CPI、10年期美债收益率；使用修订后终值而非历史 vintage。
            - 所有比较对象都是规则基准，不代表现实机构当年的真实持仓。
            """
        )

with knowledge_tab:
    render_app_header(
        title="AI 泡沫",
        gradient_word="Intelligence",
        description="把分散观点收束成统一评分，并与铁路、电气化、电信和互联网泡沫放在同一进程上比较。",
        eyebrow="DALIO FRAMEWORK × HISTORICAL ANALOGS",
        sphere_label="76",
        badges=[("当前评分", "76 / 100"), ("时间轴", "可拖动"), ("框架", "Dalio"), ("视角", "统一研判")],
    )
    render_ai_bubble_page(show_header=False)
with news_tab:
    render_app_header(
        title="每日新闻",
        gradient_word="Intelligence",
        description="自动抓取、分类、研判并归档每天的大新闻，让今天和历史任意一天的结论都可以随时调出。",
        eyebrow="DAILY NEWS × ASSET IMPACT",
        sphere_label="24H",
        badges=[("抓取频率", "每日"), ("历史档案", "可回看"), ("研判", "DeepSeek"), ("证据", "标题可追溯")],
    )
    render_news_intelligence_page(show_header=False)

with chat_tab:
    render_app_header(
        title="对话式投研",
        gradient_word="Copilot",
        description="把宏观周期、个人风险、历史回测和每日情报放进同一个上下文，回答你的资产配置问题。",
        eyebrow="DEEPSEEK × YOUR FINANCIAL CONTEXT",
        sphere_label="DS",
        badges=[("模型", "DeepSeek"), ("上下文", "四大模块"), ("数据", "联网更新"), ("用途", "研究与教学")],
    )
    section_header("ASK / AGENT", "与 Agent 对话", "围绕当前宏观环境、个人配置、历史回测和 AI 泡沫诊断继续追问。")
    question = st.text_input(
        "询问当前配置、历史回测或 AI 泡沫观点",
        placeholder="例如：Howard Marks 和 Andrew Ng 对 AI 泡沫有什么分歧？",
    )
    if st.button("询问 Agent", type="primary", disabled=not question):
        try:
            from agent import ask_agent
            with st.spinner("Agent 正在分析……"):
                st.write(ask_agent(question))
        except ModuleNotFoundError:
            st.error("尚未安装 Agent 依赖，请先运行：pip install -r requirements.txt")
        except Exception as exc:
            st.error(f"Agent 调用失败：{exc}")
