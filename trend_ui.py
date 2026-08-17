"""跨日期新闻主题与资产影响趋势页面。"""

from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from news_archive import load_trend_history
from ui_theme import section_header, style_plotly


RANGE_DAYS = {"最近 7 天": 7, "最近 30 天": 30, "最近 90 天": 90, "全部": None}
ASSET_COLORS = {"股票": "#4266E8", "债券": "#775CF0", "黄金": "#C9973B"}
LINE_DASHES = ["solid", "dash", "dot", "dashdot"]


def _filter_records(records, range_label):
    if not records or RANGE_DAYS[range_label] is None:
        return records
    latest = max(pd.Timestamp(item["date"]) for item in records)
    cutoff = latest - timedelta(days=RANGE_DAYS[range_label] - 1)
    return [item for item in records if pd.Timestamp(item["date"]) >= cutoff]


def _trend_label(change):
    if change > 0.05:
        return "上升"
    if change < -0.05:
        return "下降"
    return "大致平稳"


def render_news_trend_page():
    section_header(
        "HISTORICAL / TREND",
        "趋势分析",
        "观察已归档新闻主题与资产影响随时间的变化；页面只读取数据库，不会重新调用 AI。",
    )
    records = load_trend_history()
    if not records:
        st.info("暂无足够历史数据\n\n系统会随着每日情报归档逐步形成趋势。")
        return

    range_label = st.segmented_control(
        "时间范围",
        options=list(RANGE_DAYS),
        default="最近 30 天",
        key="news_trend_range",
    ) or "最近 30 天"
    filtered = _filter_records(records, range_label)
    topics = sorted({topic for item in filtered for topic in item.get("topics", {})})
    if not topics:
        st.info("该时间范围暂无可量化主题数据。系统会跳过缺失日期，不会补零或生成假数据。")
        return

    st.markdown("### 主题历史趋势")
    topic = st.selectbox("主题", topics, key="news_trend_topic")
    topic_rows = [
        {"date": pd.Timestamp(item["date"]), "score": item["topics"][topic]}
        for item in filtered
        if topic in item.get("topics", {})
    ]
    topic_frame = pd.DataFrame(topic_rows).sort_values("date")
    if topic_frame.empty:
        st.info("暂无足够历史数据\n\n系统会随着每日情报归档逐步形成趋势。")
        return

    current = float(topic_frame.iloc[-1].score)
    change = current - float(topic_frame.iloc[0].score)
    average = float(topic_frame.score.mean())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("当前评分", f"{current:+.2f}")
    m2.metric(f"{range_label}变化", f"{change:+.2f}")
    m3.metric("窗口平均", f"{average:+.2f}")
    m4.metric("趋势", _trend_label(change))

    topic_chart = go.Figure(
        go.Scatter(
            x=topic_frame.date,
            y=topic_frame.score,
            name=topic,
            mode="lines+markers",
            line={"width": 3, "color": "#4266E8"},
            marker={"size": 8, "color": "#FFFFFF", "line": {"color": "#4266E8", "width": 2}},
            hovertemplate="%{x|%Y-%m-%d}<br>主题评分 %{y:+.3f}<extra></extra>",
        )
    )
    topic_chart.add_hline(y=0, line_color="rgba(95,107,139,.45)", line_dash="dash")
    style_plotly(topic_chart, f"{topic}｜历史评分", 390)
    topic_chart.update_layout(hovermode="x unified", xaxis_title="日期", yaxis_title="主题评分")
    st.plotly_chart(topic_chart, width="stretch")
    st.caption(
        "主题评分来自同主题新闻已有的资产影响规则：先对每条新闻的现有资产影响等权平均，"
        "再按新闻相关度加权。范围为 -3 至 +3；不是 LLM 事后生成的观点。"
    )

    st.divider()
    st.markdown("### 资产影响趋势")
    st.caption(f"当前主题：{topic}｜只展示归档中真实存在的资产字段。")
    assets = sorted(
        {
            asset
            for item in filtered
            for asset in item.get("asset_impacts", {}).get(topic, {})
        }
    )
    if not assets:
        st.info("这个主题暂无分资产历史评分；缺失日期会自动跳过。")
        return
    default_assets = [asset for asset in ("股票", "债券", "黄金") if asset in assets] or assets[:3]
    selected_assets = st.multiselect(
        "显示资产",
        assets,
        default=default_assets,
        key="news_trend_assets",
    )
    if not selected_assets:
        st.info("请选择至少一个资产以显示趋势。")
        return

    asset_chart = go.Figure()
    table_rows = []
    for index, asset in enumerate(selected_assets):
        rows = [
            {
                "date": pd.Timestamp(item["date"]),
                "score": item["asset_impacts"][topic][asset],
            }
            for item in filtered
            if asset in item.get("asset_impacts", {}).get(topic, {})
        ]
        frame = pd.DataFrame(rows).sort_values("date")
        if frame.empty:
            continue
        asset_chart.add_trace(
            go.Scatter(
                x=frame.date,
                y=frame.score,
                name=asset,
                mode="lines+markers",
                line={
                    "width": 2.8,
                    "color": ASSET_COLORS.get(asset),
                    "dash": LINE_DASHES[index % len(LINE_DASHES)],
                },
                marker={"size": 7},
                hovertemplate=f"{asset}<br>%{{x|%Y-%m-%d}} · %{{y:+.3f}}<extra></extra>",
            )
        )
        for row in rows:
            table_rows.append({"日期": row["date"], "资产": asset, "影响评分": row["score"]})
    asset_chart.add_hline(y=0, line_color="rgba(95,107,139,.45)", line_dash="dash")
    style_plotly(asset_chart, f"{topic}｜资产影响", 420)
    asset_chart.update_layout(
        hovermode="x unified",
        xaxis_title="日期",
        yaxis_title="-3 利空 ← 0 → +3 利多",
        legend={"orientation": "h", "x": 0, "y": -0.22, "title": None},
        margin={"l": 48, "r": 24, "t": 58, "b": 88},
    )
    st.plotly_chart(asset_chart, width="stretch")
    with st.expander("查看真实历史数值"):
        st.dataframe(pd.DataFrame(table_rows).sort_values(["日期", "资产"]), hide_index=True, width="stretch")
    st.caption(
        f"当前窗口显示 {len(topic_frame)} 个真实归档日期；以最新归档日 "
        f"{topic_frame.date.max():%Y-%m-%d} 为截止日。没有记录的日期不会补零。"
    )
