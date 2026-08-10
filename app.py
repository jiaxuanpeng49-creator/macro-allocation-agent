"""宏观资产配置 Agent 的 Streamlit 图形界面。"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backtest import BENCHMARK_NAMES, run_historical_backtest
from bubble_history import append_news_snapshot
from bubble_ui import render_ai_bubble_page
from news_intelligence import generate_deepseek_news_analysis, load_news_intelligence, refresh_news_intelligence
from personal_allocation import OCCUPATION_STABILITY, run_personalized_allocation
from pipeline import run_macro_analysis
from ui_theme import apply_theme, render_app_header, section_header, style_plotly

st.set_page_config(page_title="宏观资产配置 Agent", layout="wide", initial_sidebar_state="collapsed")
apply_theme()
render_app_header()

combined_tab, history_tab, knowledge_tab, news_tab, chat_tab = st.tabs(
    ["综合配置建议", "30年历史回测", "AI泡沫知识库", "每日新闻情报", "与 Agent 对话"]
)

with combined_tab:
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
    st.divider()
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
            marker={"line": {"color": "#0F172A", "width": 3}},
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
    render_ai_bubble_page()
with news_tab:
    section_header(
        "DAILY / NEWS INTELLIGENCE",
        "每日宏观与资产新闻情报",
        "抓取最新公开新闻，按主题归类，并把标题信号转换为资产方向、增长/通胀影响和AI泡沫增量判断。",
    )
    report = load_news_intelligence()
    refresh_col, ai_col, status_col = st.columns([1, 1, 2])
    if refresh_col.button("立即抓取最新新闻", type="primary", width="stretch"):
        try:
            with st.spinner("正在连接新闻源、去重并生成影响分析……"):
                report = refresh_news_intelligence(force=True)
                append_news_snapshot(report)
            st.success(f"已更新 {report['news_count']} 条有效新闻，并写入今天的泡沫判断快照。")
        except Exception as exc:
            st.error(f"新闻刷新失败：{exc}。请稍后重试；已有历史数据不会被覆盖。")
    if ai_col.button("DeepSeek 综合研判", width="stretch", disabled=not report):
        try:
            with st.spinner("DeepSeek 正在聚合主要新闻簇与资产、周期影响……"):
                report = generate_deepseek_news_analysis(report)
            st.success("DeepSeek 综合研判已更新，并保留透明规则评分作为审计底稿。")
        except Exception as exc:
            st.error(f"DeepSeek 分析失败：{exc}。新闻与规则底稿仍可正常使用。")
    status_col.caption("每日任务会依次抓取新闻、更新泡沫分数并调用DeepSeek；本地按钮可随时盘中刷新。")

    if not report:
        st.info("尚未生成新闻快照。点击“立即抓取最新新闻”开始第一次更新。")
    else:
        if report.get("stale"):
            st.warning(f"新闻源暂时不可用，当前展示缓存快照。最近错误：{report.get('refresh_error', '未知错误')}")
        n1, n2, n3, n4 = st.columns(4)
        n1.metric("有效新闻", report["news_count"])
        n2.metric("数据来源", report["provider"])
        n3.metric("AI泡沫增量压力", f"{report['bubble_pressure']:+.2f}")
        n4.metric("更新时间（UTC）", pd.to_datetime(report["fetched_at"]).strftime("%m-%d %H:%M"))
        if report.get("deepseek_analysis"):
            with st.container(border=True):
                analysis_time = pd.to_datetime(report["deepseek_analyzed_at"]).strftime("%m-%d %H:%M UTC")
                st.markdown("### DeepSeek 新闻综合研判")
                st.caption(
                    f"模型 {report.get('deepseek_model', 'deepseek-chat')}｜分析时间 {analysis_time}｜"
                    f"使用 {report.get('deepseek_evidence_count', 0)} 条精选标题与规则底稿"
                )
                st.markdown(report["deepseek_analysis"])
        else:
            st.info("尚未生成 DeepSeek 综合研判。点击上方按钮后，会把分散新闻合成一个资产与周期结论。")

        st.info("**透明规则底稿：** " + report["summary"] + " " + report["bubble_summary"])

        category_col, impact_col = st.columns([3, 2])
        category_data = pd.DataFrame(
            sorted(report["category_counts"].items(), key=lambda item: item[1]), columns=["category", "count"]
        )
        category_chart = go.Figure(go.Bar(
            x=category_data["count"], y=category_data["category"], orientation="h",
            text=category_data["count"], textposition="auto", marker_color="#3B82F6",
        ))
        style_plotly(category_chart, "新闻主题分布", 360)
        category_chart.update_layout(showlegend=False, xaxis_title="新闻数量", yaxis_title=None)
        category_col.plotly_chart(category_chart, width="stretch")

        impact_values = report["asset_impact"]
        impact_chart = go.Figure(go.Bar(
            x=list(impact_values), y=list(impact_values.values()),
            text=[f"{value:+.2f}" for value in impact_values.values()], textposition="auto",
            marker_color=["#10B981" if value > 0 else "#F87171" if value < 0 else "#94A3B8" for value in impact_values.values()],
        ))
        style_plotly(impact_chart, "资产影响方向（-3利空，+3利多）", 360)
        impact_chart.update_layout(showlegend=False, yaxis={"range": [-3, 3], "zeroline": True})
        impact_col.plotly_chart(impact_chart, width="stretch")

        cycle_left, cycle_right = st.columns(2)
        cycle_left.metric("增长方向", f"{report['cycle_impact']['growth']:+.2f}")
        cycle_right.metric("通胀方向", f"{report['cycle_impact']['inflation']:+.2f}")
        st.caption("周期含义：" + report["cycle_impact"]["interpretation"])

        filter_col, asset_col = st.columns(2)
        categories = ["全部"] + sorted(report["category_counts"])
        news_category = filter_col.selectbox("按新闻主题筛选", categories, key="news_category")
        news_asset = asset_col.selectbox("按主要影响资产筛选", ["全部", "股票", "债券", "黄金"], key="news_asset")
        filtered_news = report["articles"]
        if news_category != "全部":
            filtered_news = [item for item in filtered_news if item["category"] == news_category]
        if news_asset != "全部":
            filtered_news = [item for item in filtered_news if abs(item["asset_impact"][news_asset]) >= 1]

        st.markdown(f"### 新闻明细｜{len(filtered_news)} 条")
        for item in filtered_news[:25]:
            with st.container(border=True):
                title_col, link_col = st.columns([4, 1])
                title_col.markdown(f"#### {item['title']}")
                title_col.caption(f"{item['category']}｜{item['source']}｜{pd.to_datetime(item['published_at']).strftime('%m-%d %H:%M UTC')}")
                link_col.link_button("打开原始新闻", item["url"], width="stretch")
                st.write(item["impact_summary"])
                impacts = "｜".join(f"{asset} {value:+d}" for asset, value in item["asset_impact"].items())
                st.caption(impacts)

        with st.expander("自动更新、API和模型边界"):
            st.markdown(
                """
                - 配置 `NEWSAPI_KEY` 后优先使用 NewsAPI；未配置时使用 Google News RSS 作为研究用途回退源。
                - `.github/workflows/daily-intelligence.yml` 已准备每日任务，但本地满意并发布 GitHub 后才会真正启用。
                - 自动分析只读取标题、来源、时间和链接，不复制新闻正文。
                - DeepSeek 只接收精选标题、来源、时间、链接和规则底稿，不假装读取新闻正文。
                - 每日自动流程会先保存透明关键词规则，再生成DeepSeek综合研判；二者都保留，便于发现分歧。
                """
            )
            for limitation in report["limitations"]:
                st.markdown(f"- {limitation}")

with chat_tab:
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
