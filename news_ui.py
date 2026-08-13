"""每日新闻情报与历史档案的 Streamlit 页面。"""

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from bubble_history import append_news_snapshot
from news_archive import (
    archive_daily_report,
    archive_overview,
    list_archive_dates,
    load_archive_series,
    load_archived_report,
)
from news_intelligence import (
    generate_deepseek_news_analysis,
    load_news_intelligence,
    refresh_news_intelligence,
)
from ui_theme import section_header, style_plotly


def _date_label(value, latest_date=None):
    parsed = datetime.strptime(value, "%Y-%m-%d")
    label = parsed.strftime("%Y年%m月%d日")
    return f"{label} · 最新" if value == latest_date else label


def _archive_current_report(report):
    if not report:
        return
    report_date = report.get("as_of_date") or report["fetched_at"][:10]
    saved = load_archived_report(report_date)
    if (
        not saved
        or saved.get("fetched_at") != report.get("fetched_at")
        or saved.get("deepseek_analyzed_at") != report.get("deepseek_analyzed_at")
    ):
        archive_daily_report(report)


def _render_archive_trend():
    series = load_archive_series()
    if len(series) < 2:
        st.caption("数据库积累到两天后，这里会自动出现资产风向与泡沫压力趋势图。")
        return
    frame = pd.DataFrame(series)
    frame["date"] = pd.to_datetime(frame["date"])
    figure = go.Figure()
    for field, label, dash in [
        ("stock", "股票", "solid"),
        ("bond", "债券", "dash"),
        ("gold", "黄金", "dot"),
        ("bubble_pressure", "AI泡沫压力", "dashdot"),
    ]:
        figure.add_trace(
            go.Scatter(
                x=frame["date"],
                y=frame[field],
                name=label,
                mode="lines+markers",
                line={"width": 2.4, "dash": dash},
                marker={"size": 6},
            )
        )
    style_plotly(figure, "每日资产风向与AI泡沫压力", 380)
    figure.update_layout(hovermode="x unified", yaxis_title="-3 利空 ← 0 → +3 利多")
    st.plotly_chart(figure, width="stretch")
    with st.expander("查看历史数值表"):
        table = frame.rename(
            columns={
                "date": "日期",
                "news_count": "新闻数",
                "stock": "股票",
                "bond": "债券",
                "gold": "黄金",
                "growth": "增长",
                "inflation": "通胀",
                "bubble_pressure": "AI泡沫压力",
            }
        )
        st.dataframe(table, hide_index=True, width="stretch")


def _render_report(report, selected_date, latest_date):
    is_latest = selected_date == latest_date
    view_badge = "最新快照" if is_latest else "历史归档"
    st.markdown(f"### {view_badge}｜{_date_label(selected_date)}")
    st.caption(
        "数据库保存当日聚合摘要、资产风向、模型结论与精简标题证据，不保存新闻正文。"
    )

    if report.get("stale"):
        st.warning(f"新闻源暂时不可用，当前展示缓存快照。最近错误：{report.get('refresh_error', '未知错误')}")

    n1, n2, n3, n4 = st.columns(4)
    n1.metric("有效新闻", report["news_count"])
    n2.metric("数据来源", report["provider"])
    n3.metric("AI泡沫增量压力", f"{report['bubble_pressure']:+.2f}")
    n4.metric("抓取时间（UTC）", pd.to_datetime(report["fetched_at"]).strftime("%m-%d %H:%M"))

    if report.get("deepseek_analysis"):
        with st.container(border=True):
            analyzed_at = report.get("deepseek_analyzed_at")
            analysis_time = pd.to_datetime(analyzed_at).strftime("%m-%d %H:%M UTC") if analyzed_at else "未知"
            st.markdown("### DeepSeek 新闻综合研判")
            st.caption(
                f"模型 {report.get('deepseek_model', 'deepseek-chat')}｜分析时间 {analysis_time}｜"
                f"使用 {report.get('deepseek_evidence_count', 0)} 条精选标题与规则底稿"
            )
            st.markdown(report["deepseek_analysis"])
    else:
        st.info("这一天尚未生成 DeepSeek 综合研判，当前展示可审计的规则摘要与风向指标。")

    st.info("**透明规则底稿：** " + report["summary"] + " " + report["bubble_summary"])

    category_col, impact_col = st.columns([3, 2])
    category_data = pd.DataFrame(
        sorted(report["category_counts"].items(), key=lambda item: item[1]),
        columns=["category", "count"],
    )
    category_chart = go.Figure(
        go.Bar(
            x=category_data["count"],
            y=category_data["category"],
            orientation="h",
            text=category_data["count"],
            textposition="auto",
            marker_color="#4266E8",
        )
    )
    style_plotly(category_chart, "新闻主题分布", 360)
    category_chart.update_layout(showlegend=False, xaxis_title="新闻数量", yaxis_title=None)
    category_col.plotly_chart(category_chart, width="stretch")

    impact_values = report["asset_impact"]
    impact_chart = go.Figure(
        go.Bar(
            x=list(impact_values),
            y=list(impact_values.values()),
            text=[f"{value:+.2f}" for value in impact_values.values()],
            textposition="auto",
            marker_color=[
                "#31836D" if value > 0 else "#C34F67" if value < 0 else "#8792B0"
                for value in impact_values.values()
            ],
        )
    )
    style_plotly(impact_chart, "资产影响方向（-3利空，+3利多）", 360)
    impact_chart.update_layout(showlegend=False, yaxis={"range": [-3, 3], "zeroline": True})
    impact_col.plotly_chart(impact_chart, width="stretch")

    cycle_left, cycle_right = st.columns(2)
    cycle_left.metric("增长方向", f"{report['cycle_impact']['growth']:+.2f}")
    cycle_right.metric("通胀方向", f"{report['cycle_impact']['inflation']:+.2f}")
    st.caption("周期含义：" + report["cycle_impact"]["interpretation"])

    articles = report.get("articles", [])
    if articles:
        filter_col, asset_col = st.columns(2)
        categories = ["全部"] + sorted(report["category_counts"])
        news_category = filter_col.selectbox("按新闻主题筛选", categories, key="news_category")
        news_asset = asset_col.selectbox(
            "按主要影响资产筛选", ["全部", "股票", "债券", "黄金"], key="news_asset"
        )
        filtered_news = articles
        if news_category != "全部":
            filtered_news = [item for item in filtered_news if item["category"] == news_category]
        if news_asset != "全部":
            filtered_news = [item for item in filtered_news if abs(item["asset_impact"][news_asset]) >= 1]

        st.markdown(f"### 当天标题证据｜{len(filtered_news)} 条")
        st.caption("这里只展示标题、来源、时间与规则影响；新闻正文不会保存到数据库。")
        for item in filtered_news[:25]:
            with st.container(border=True):
                title_col, link_col = st.columns([4, 1])
                title_col.markdown(f"#### {item['title']}")
                title_col.caption(
                    f"{item['category']}｜{item['source']}｜"
                    f"{pd.to_datetime(item['published_at']).strftime('%m-%d %H:%M UTC')}"
                )
                link_col.link_button("打开原始新闻", item["url"], width="stretch")
                st.write(item["impact_summary"])
                impacts = "｜".join(f"{asset} {value:+d}" for asset, value in item["asset_impact"].items())
                st.caption(impacts)


def render_news_intelligence_page(show_header=True):
    if show_header:
        section_header(
            "DAILY / NEWS ARCHIVE",
            "每日宏观与资产新闻情报",
            "每天自动抓取并归档摘要、资产风向、周期判断与AI泡沫增量；可按日期回看历史结论。",
        )
    latest_report = load_news_intelligence()
    if latest_report:
        _archive_current_report(latest_report)

    refresh_col, ai_col, status_col = st.columns([1, 1, 2])
    if refresh_col.button("立即抓取今日新闻", type="primary", width="stretch"):
        try:
            with st.spinner("正在连接新闻源、去重并生成影响分析……"):
                latest_report = refresh_news_intelligence(force=True)
                append_news_snapshot(latest_report)
                _archive_current_report(latest_report)
            st.success(f"已更新 {latest_report['news_count']} 条有效新闻，并归档今日规则摘要。")
        except Exception as exc:
            st.error(f"新闻刷新失败：{exc}。请稍后重试；已有历史档案不会被覆盖。")

    if ai_col.button("生成今日 DeepSeek 研判", width="stretch", disabled=not latest_report):
        try:
            with st.spinner("DeepSeek 正在聚合主要新闻簇与资产、周期影响……"):
                latest_report = generate_deepseek_news_analysis(latest_report)
                _archive_current_report(latest_report)
            st.success("今日 DeepSeek 研判已完成并写入数据库。")
        except Exception as exc:
            st.error(f"DeepSeek 分析失败：{exc}。新闻与规则档案仍可正常使用。")
    status_col.caption("自动任务每日抓取一次并更新同一天记录；手动刷新不会产生重复日期。")

    dates = list_archive_dates()
    overview = archive_overview()
    if not dates:
        st.info("数据库还没有记录。点击“立即抓取今日新闻”创建第一天的情报档案。")
        return

    latest_date = latest_report.get("as_of_date") if latest_report else dates[0]
    database_col, range_col, selector_col = st.columns([1, 1, 2])
    database_col.metric("数据库已归档", f"{overview['day_count']} 天")
    date_range = (
        _date_label(overview["first_date"])
        if overview["first_date"] == overview["last_date"]
        else f"{overview['first_date']} → {overview['last_date']}"
    )
    range_col.metric("历史范围", date_range)
    selected_date = selector_col.selectbox(
        "选择已有情报日期",
        dates,
        format_func=lambda value: _date_label(value, latest_date),
        help="只显示数据库中已经完成归档的日期。",
    )

    if latest_report and selected_date == latest_report.get("as_of_date"):
        selected_report = latest_report
    else:
        selected_report = load_archived_report(selected_date)
    if not selected_report:
        st.warning("没有找到这一天的档案，请选择其他日期。")
        return


    if not selected_report.get("deepseek_analysis") and selected_report.get("articles"):
        st.warning("该日期已有标题证据，但综合研判尚未生成。定时任务会自动补齐，也可以现在生成。")
        if st.button(
            f"补生成 {_date_label(selected_date)} DeepSeek 综合研判",
            key=f"backfill_analysis_{selected_date}",
            width="stretch",
        ):
            try:
                with st.spinner("DeepSeek 正在根据当天标题证据补生成历史研判……"):
                    selected_report = generate_deepseek_news_analysis(
                        selected_report,
                        persist_cache=selected_date == latest_date,
                    )
                    archive_daily_report(selected_report)
                st.success("该日期的综合研判已生成并写入数据库。")
            except Exception as exc:
                st.error(f"历史研判生成失败：{exc}")

    _render_report(selected_report, selected_date, latest_date)

    st.divider()
    st.markdown("### 历史风向轨迹")
    _render_archive_trend()

    with st.expander("自动更新、数据库与模型边界"):
        st.markdown(
            """
            - SQLite 数据库按日期保存一条聚合记录；同一天再次抓取会更新该记录，不会重复堆积。
            - 数据库保存主题数量、资产风向、周期指标、泡沫压力、综合摘要，以及最多60条精简标题证据；不保存新闻正文。
            - 配置 `NEWSAPI_KEY` 后优先使用 NewsAPI；未配置时使用 Google News RSS 作为研究用途回退源。
            - DeepSeek 只接收精选标题、来源、时间、链接和规则底稿，不假装读取新闻正文。
            - 每日自动流程会先保存透明关键词规则，再生成 DeepSeek 综合研判；二者都保留，便于发现分歧。
            - 定时任务还会自动扫描“已有标题证据但缺少综合研判”的历史日期，并逐日补齐。
            """
        )
        for limitation in selected_report.get("limitations", []):
            st.markdown(f"- {limitation}")
