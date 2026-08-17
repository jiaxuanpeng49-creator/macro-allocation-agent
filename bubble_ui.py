"""AI泡沫知识库的分层、低噪音图形界面。"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ai_bubble_diagnosis import unified_ai_bubble_diagnosis
from bubble_history import load_bubble_history
from knowledge_base import load_knowledge, search_knowledge
from technology_bubbles import (
    ai_historical_conclusion,
    all_bubble_series,
    load_normalized_price_series,
    price_series_availability,
)
from ui_theme import section_header, style_plotly


def _render_ai_timeline(diagnosis, analog_df):
    st.markdown("### AI技术与资本热度")
    st.caption("1956年至今｜白色大节点有独立史料，蓝色小节点为相邻史料之间的模型插值。")
    ai_df = analog_df.loc[analog_df.id == "ai"].copy()
    ai_df.loc[ai_df.year == ai_df.year.max(), ["score", "phase"]] = [diagnosis["stage_score"], diagnosis["stage"]]

    chart = go.Figure()
    chart.add_hrect(y0=0, y1=61, fillcolor="rgba(16,185,129,.045)", line_width=0)
    chart.add_hrect(y0=61, y1=84, fillcolor="rgba(245,158,11,.065)", line_width=0)
    chart.add_hrect(y0=84, y1=100, fillcolor="rgba(248,113,113,.075)", line_width=0)
    chart.add_trace(go.Scatter(
        x=ai_df.year,
        y=ai_df.score,
        mode="lines+markers",
        line={"width": 3, "color": "#4266E8", "shape": "spline", "smoothing": 0.55},
        marker={
            "size": [10 if value else 4 for value in ai_df.is_anchor],
            "color": ["#FFFFFF" if value else "#4266E8" for value in ai_df.is_anchor],
            "line": {"color": "#4266E8", "width": 2},
        },
        customdata=ai_df[["year", "phase", "event", "is_anchor"]],
        hovertemplate="%{customdata[0]}年 · %{y:.0f}/100<br>%{customdata[1]}<br>%{customdata[2]}<extra></extra>",
    ))
    style_plotly(chart, "AI长期轨迹", 390)
    chart.update_layout(
        showlegend=False,
        dragmode="select",
        margin={"l": 42, "r": 18, "t": 58, "b": 48},
        xaxis={"title": None, "dtick": 10, "tickangle": 0, "showgrid": False},
        yaxis={"range": [0, 100], "title": "热度", "dtick": 20},
    )
    event = st.plotly_chart(chart, width="stretch", key="ai_timeline_v2", on_select="rerun", selection_mode="points")
    clicked_year = None
    if event and event.selection.points:
        clicked_year = int(event.selection.points[0].get("customdata", [0])[0])

    years = ai_df.year.astype(int).tolist()
    selected_year = st.select_slider(
        "拖动年份查看当时判断",
        options=years,
        value=clicked_year if clicked_year in years else years[-1],
        key="ai_year_v2",
    )
    selected = ai_df.loc[ai_df.year == selected_year].iloc[0]
    c1, c2, c3 = st.columns([1, 1, 2])
    c1.metric("年份", str(selected_year))
    c2.metric("热度", f"{selected.score:.0f}/100")
    c3.metric("阶段", selected.phase)
    with st.container(border=True):
        st.markdown(f"**{selected.event}**")
        st.write(selected.rationale)
        nature = "独立史料锚点" if selected.is_anchor else "相邻史料锚点之间的模型插值"
        st.caption(f"数据性质：{nature}")
        if selected.source_url:
            st.link_button("查看史料来源", selected.source_url)

    with st.expander("近期放大镜｜2025年至今"):
        history = load_bubble_history()
        recent_df = pd.DataFrame(history["snapshots"])
        recent_df["date_value"] = pd.to_datetime(recent_df.date)
        recent = go.Figure(go.Scatter(
            x=recent_df.date_value,
            y=recent_df.score,
            mode="lines+markers",
            line={"width": 2.5, "color": "#4266E8"},
            marker={"size": 8},
            customdata=recent_df[["date", "stage"]],
            hovertemplate="%{customdata[0]} · %{y}/100<br>%{customdata[1]}<extra></extra>",
        ))
        style_plotly(recent, "近期更新", 300)
        recent.update_layout(
            showlegend=False,
            margin={"l": 40, "r": 16, "t": 52, "b": 40},
            yaxis={"range": [0, 100], "title": "热度"},
            xaxis={"title": None},
        )
        st.plotly_chart(recent, width="stretch")
        snapshot_date = st.select_slider(
            "选择近期快照", recent_df.date.tolist(), value=recent_df.date.iloc[-1], key="recent_date_v2"
        )
        snapshot = next(item for item in history["snapshots"] if item["date"] == snapshot_date)
        st.info(f"**{snapshot['date']}｜{snapshot['score']}/100：** {snapshot['judgment']}")


def _render_history_map(analogs, analog_df, diagnosis):
    st.markdown("### 两百年技术泡沫地图")
    st.caption("每一行是一轮独立技术浪潮。线段表示观察区间，圆点表示有史料支持的重要转折；详细文字只在悬浮时显示。")
    bubble_order = ["railway", "telegraph", "electricity", "internet_telecom", "ai"]
    labels = []
    history_map = go.Figure()
    for bubble_id in bubble_order:
        frame = analog_df.loc[analog_df.id == bubble_id]
        label = frame.short_name.iloc[0]
        labels.append(label)
        color = frame.color.iloc[0]
        anchors = frame.loc[frame.is_anchor]
        history_map.add_trace(go.Scatter(
            x=[frame.year.min(), frame.year.max()],
            y=[label, label],
            mode="lines",
            line={"width": 12, "color": color},
            opacity=0.22,
            hoverinfo="skip",
            showlegend=False,
        ))
        history_map.add_trace(go.Scatter(
            x=anchors.year,
            y=[label] * len(anchors),
            mode="markers",
            marker={
                "size": [9 + value / 16 for value in anchors.score],
                "color": anchors.score,
                "colorscale": [[0, "#38BDF8"], [.65, "#FBBF24"], [1, "#FB7185"]],
                "cmin": 0,
                "cmax": 100,
                "line": {"color": color, "width": 1.5},
            },
            customdata=anchors[["year", "score", "phase", "event"]],
            hovertemplate="%{customdata[0]}年 · %{customdata[1]:.0f}/100<br>%{customdata[2]}<br>%{customdata[3]}<extra>" + label + "</extra>",
            showlegend=False,
        ))
    style_plotly(history_map, "历史分布", 390)
    history_map.update_layout(
        margin={"l": 24, "r": 18, "t": 54, "b": 48},
        xaxis={"title": "年份", "dtick": 25, "showgrid": True, "gridcolor": "rgba(148,163,184,.12)"},
        yaxis={"title": None, "categoryorder": "array", "categoryarray": labels[::-1]},
        hovermode="closest",
    )
    st.plotly_chart(history_map, width="stretch")
    st.caption("圆点越大代表标准化热度越高；颜色由蓝到黄再到红。图表表达相对阶段，不代表历史市场价格指数。")

    st.divider()
    comparison_mode = st.segmented_control(
        "比较模式",
        options=["生命周期对齐", "资产价格对齐"],
        default="生命周期对齐",
        key="bubble_compare_mode",
    ) or "生命周期对齐"
    if comparison_mode == "资产价格对齐":
        _render_asset_price_map(analogs)
        return

    st.markdown("### AI与单一历史周期对比")
    st.caption("一次只比较一个对象，避免五条曲线缠绕。所有曲线把资本加速年设为 T=0。")
    choices = {item["name"]: item["id"] for item in analogs["bubbles"] if item["id"] != "ai"}
    selected_name = st.selectbox("选择历史参照", list(choices), index=3, key="bubble_analog_v2")
    selected_id = choices[selected_name]
    ai_frame = analog_df.loc[(analog_df.id == "ai") & (analog_df.relative_year >= -10) & (analog_df.relative_year <= 20)].copy()
    analog_frame = analog_df.loc[(analog_df.id == selected_id) & (analog_df.relative_year >= -10) & (analog_df.relative_year <= 20)].copy()
    analog_color = analog_frame.color.iloc[0]

    compare = go.Figure()
    compare.add_trace(go.Scatter(
        x=analog_frame.relative_year,
        y=analog_frame.score,
        mode="lines",
        line={"width": 3, "color": analog_color, "dash": "dash", "shape": "spline", "smoothing": .45},
        name=selected_name,
        customdata=analog_frame[["year", "phase"]],
        hovertemplate="T%{x:+d} · %{y:.0f}/100<br>原始年份 %{customdata[0]}<br>%{customdata[1]}<extra>历史参照</extra>",
    ))
    compare.add_trace(go.Scatter(
        x=ai_frame.relative_year,
        y=ai_frame.score,
        mode="lines",
        line={"width": 4, "color": "#4266E8", "shape": "spline", "smoothing": .45},
        name="AI",
        customdata=ai_frame[["year", "phase"]],
        hovertemplate="T%{x:+d} · %{y:.0f}/100<br>原始年份 %{customdata[0]}<br>%{customdata[1]}<extra>AI</extra>",
    ))
    ai_today_t = int(ai_frame.relative_year.max())
    ai_today = ai_frame.loc[ai_frame.relative_year == ai_today_t].iloc[0]
    compare.add_trace(go.Scatter(
        x=[ai_today_t], y=[diagnosis["stage_score"]], mode="markers",
        marker={"size": 15, "symbol": "diamond", "color": "#FFFFFF", "line": {"color": "#4266E8", "width": 3}},
        name="AI今天", hovertemplate=f"AI今天 · T+{ai_today_t}<br>{diagnosis['stage_score']}/100<extra></extra>",
    ))
    style_plotly(compare, "生命周期对齐", 390)
    compare.update_layout(
        margin={"l": 42, "r": 42, "t": 58, "b": 82},
        hovermode="closest",
        xaxis={"title": "距资本加速起点的年数（T）", "dtick": 5, "range": [-10, 20.5]},
        yaxis={"title": "热度", "range": [0, 100], "dtick": 20},
        legend={"orientation": "h", "x": 0, "y": -0.24, "title": None},
    )
    st.plotly_chart(compare, width="stretch")

    analog_same_t = analog_frame.iloc[(analog_frame.relative_year - ai_today_t).abs().argsort()[:1]].iloc[0]
    k1, k2, k3 = st.columns(3)
    k1.metric("AI今天", f"{diagnosis['stage_score']}/100", f"T+{ai_today_t}")
    k2.metric(selected_name, f"{analog_same_t.score:.0f}/100", f"T{int(analog_same_t.relative_year):+d}")
    k3.metric("同阶段热度差", f"{diagnosis['stage_score'] - analog_same_t.score:+.0f}分")
    st.warning("**统一结论：** " + ai_historical_conclusion(diagnosis["stage_score"]))

    selected_meta = next(item for item in analogs["bubbles"] if item["id"] == selected_id)
    with st.expander(f"查看{selected_name}的史料锚点与模型边界"):
        st.write(f"分类：**{selected_meta['classification']}**｜置信度：**{selected_meta['confidence']}**")
        st.caption(analogs["methodology"])
        table = pd.DataFrame(selected_meta["anchors"])[["year", "score", "phase", "event", "source_url"]]
        st.dataframe(table, hide_index=True, width="stretch")


def _render_asset_price_map(analogs):
    st.markdown("### 200 年技术泡沫地图")
    st.caption(
        "将不同技术革命的真实代理资产价格统一到 T0 = 100。只统一起点，不统一峰值，"
        "不使用热度曲线代替价格，也不做正态拟合。"
    )
    try:
        price_frame, errors = load_normalized_price_series()
    except ValueError as exc:
        st.error(f"历史价格数据结构不完整：{exc}")
        return
    availability = price_series_availability(price_frame)
    if price_frame.empty:
        st.info(
            "暂无可审计的历史资产价格序列\n\n"
            "当前项目只有铁路、电报、电力、互联网与 AI 的史料热度锚点，尚未确认各周期的 proxy asset、"
            "精确 T0 日期和真实价格序列。为避免伪造比较，本图暂不绘制曲线。"
        )
        with st.expander("查看当前数据缺口", expanded=True):
            st.dataframe(availability, hide_index=True, width="stretch")
            st.caption(
                "后续数据文件需提供 bubble_id、date、price、proxy_asset、t0_date、source_url。"
                "归一化会由后端自动计算，前端不硬编码历史价格。"
            )
        return

    meta = {item["id"]: item for item in analogs["bubbles"]}
    available_ids = [bubble_id for bubble_id in price_frame.bubble_id.unique() if bubble_id in meta]
    labels = {bubble_id: meta[bubble_id]["name"] for bubble_id in available_ids}
    default_ids = [bubble_id for bubble_id in ("ai", "internet_telecom") if bubble_id in available_ids]
    selected_ids = st.multiselect(
        "历史参照",
        available_ids,
        default=default_ids or available_ids[:2],
        format_func=labels.get,
        key="bubble_price_selection",
    )
    if not selected_ids:
        st.info("请选择至少一个已有真实价格数据的技术周期。")
        return

    chart = go.Figure()
    metrics = []
    for bubble_id in selected_ids:
        frame = price_frame.loc[price_frame.bubble_id == bubble_id].sort_values("date")
        color = meta[bubble_id]["color"]
        proxy = frame.proxy_asset.iloc[0]
        chart.add_trace(
            go.Scatter(
                x=frame.relative_year,
                y=frame.normalized_price,
                mode="lines",
                line={"width": 3.5 if bubble_id == "ai" else 2.5, "color": color},
                name=meta[bubble_id]["short_name"],
                customdata=frame[["date", "price", "proxy_asset"]],
                hovertemplate=(
                    "T%{x:+.1f} · %{y:.1f}<br>%{customdata[0]|%Y-%m-%d}<br>"
                    "原始价格 %{customdata[1]:.3f}<br>%{customdata[2]}<extra></extra>"
                ),
            )
        )
        peak_index = frame.normalized_price.idxmax()
        peak = frame.loc[peak_index]
        drawdown = frame.normalized_price / frame.normalized_price.cummax() - 1
        metrics.append(
            {
                "技术周期": meta[bubble_id]["name"],
                "资产代理": proxy,
                "T0日期": f"{frame.t0_date.iloc[0]:%Y-%m-%d}",
                "峰值（T0=100）": round(float(peak.normalized_price), 1),
                "峰值T": round(float(peak.relative_year), 1),
                "最大回撤": f"{drawdown.min():.1%}",
                "价格点数": len(frame),
                "数据来源": frame.source_url.dropna().iloc[0] if frame.source_url.notna().any() else "",
            }
        )
        if bubble_id == "ai":
            today = frame.iloc[-1]
            chart.add_trace(
                go.Scatter(
                    x=[today.relative_year],
                    y=[today.normalized_price],
                    mode="markers",
                    marker={"size": 16, "symbol": "diamond", "color": "#FFFFFF", "line": {"color": color, "width": 3}},
                    name="AI今天",
                    hovertemplate=f"AI今天 · T%{{x:+.1f}}<br>%{{y:.1f}}<br>{proxy}<extra></extra>",
                )
            )
    chart.add_hline(y=100, line_color="rgba(95,107,139,.45)", line_dash="dash")
    style_plotly(chart, "技术泡沫资产价格对齐", 470)
    chart.update_layout(
        hovermode="closest",
        xaxis_title="距资本加速起点的年数（T）",
        yaxis_title="归一化资产价格（T0 = 100）",
        legend={"orientation": "h", "x": 0, "y": -0.2, "title": None},
        margin={"l": 48, "r": 24, "t": 58, "b": 92},
    )
    st.plotly_chart(chart, width="stretch")
    st.caption(
        "显示 FRED 收录的 Nasdaq 指数月末价格及精确 T0 观察值；没有峰值缩放、曲线拟合或未来外推。"
    )
    st.dataframe(
        pd.DataFrame(metrics),
        hide_index=True,
        width="stretch",
        column_config={"数据来源": st.column_config.LinkColumn("数据来源", display_text="打开 FRED")},
    )
    if errors:
        st.warning("部分价格序列未展示：" + "；".join(f"{key}：{value}" for key, value in errors.items()))


def _render_dalio(diagnosis):
    st.markdown("### Dalio公开框架复刻")
    st.caption("只展示统一指标诊断，不与历史时间图混在同一视觉层级。")
    cycle_col, indicator_col = st.columns([3, 2])
    stages = diagnosis["stages"]
    cycle_y = [0.08, 0.35, 0.72, 0.96, 0.30, 0.48]
    cycle = go.Figure(go.Scatter(
        x=list(range(len(stages))), y=cycle_y, mode="lines+markers",
        line={"shape": "spline", "width": 3, "color": "#4266E8"},
        marker={"size": 8}, hovertemplate="%{text}<extra></extra>", text=stages,
    ))
    current = diagnosis["stage_index"]
    cycle.add_trace(go.Scatter(
        x=[current], y=[cycle_y[current]], mode="markers",
        marker={"size": 16, "symbol": "diamond", "color": "#FFFFFF", "line": {"color": "#4266E8", "width": 3}},
        hovertemplate="当前AI<extra></extra>",
    ))
    style_plotly(cycle, "长期周期位置", 350)
    cycle.update_layout(
        showlegend=False,
        margin={"l": 12, "r": 12, "t": 54, "b": 74},
        xaxis={"tickmode": "array", "tickvals": list(range(len(stages))), "ticktext": stages, "tickangle": -18},
        yaxis={"visible": False},
    )
    cycle_col.plotly_chart(cycle, width="stretch")

    indicators = pd.DataFrame(diagnosis["indicators"])
    bars = go.Figure(go.Bar(
        x=indicators.score, y=indicators.name, orientation="h",
        text=[f"{score}/5" for score in indicators.score], textposition="inside",
        marker_color="#4266E8",
        customdata=indicators.assessment,
        hovertemplate="%{y} · %{x}/5<br>%{customdata}<extra></extra>",
    ))
    style_plotly(bars, "六项指标", 350)
    bars.update_layout(
        showlegend=False,
        margin={"l": 10, "r": 18, "t": 54, "b": 34},
        xaxis={"range": [0, 5], "dtick": 1, "title": None},
        yaxis={"autorange": "reversed", "title": None},
    )
    indicator_col.plotly_chart(bars, width="stretch")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("#### 向顶部推进")
            for trigger in diagnosis["next_stage_triggers"]["toward_top"]:
                st.markdown(f"- {trigger}")
    with right:
        with st.container(border=True):
            st.markdown("#### 转向健康建设")
            for trigger in diagnosis["next_stage_triggers"]["toward_healthy_buildout"]:
                st.markdown(f"- {trigger}")

    with st.expander("六项指标的证据、来源和模型边界"):
        for item in diagnosis["indicators"]:
            st.markdown(f"**{item['name']}｜{item['score']}/5｜{item['assessment']}**")
            st.write(item["evidence"])
            st.markdown(f"[查看来源]({item['source_url']})")
        st.divider()
        for note in diagnosis["limitations"]:
            st.markdown(f"- {note}")


def _render_views():
    st.markdown("### 人物观点检索")
    st.caption("观点只用于解释分歧；最终结论仍由可观察指标与历史比较共同生成。")
    query_col, stance_col = st.columns([2, 1])
    query = query_col.text_input("检索观点", value="AI泡沫 资本开支 估值", key="knowledge_query_v2")
    stance = stance_col.selectbox("观点方向", ["全部", "泡沫", "看多", "非理性", "应用层"], key="stance_v2")
    results = search_knowledge(query, top_k=6, stance=None if stance == "全部" else stance)
    if not results:
        st.warning("当前筛选没有匹配观点，请更换关键词或选择“全部”。")
    for index, item in enumerate(results):
        label = f"{item['person']}｜{item['stance']}｜{item['date']}"
        with st.expander(label, expanded=index == 0):
            st.caption(f"{item['role']}｜来源可信度 {item['confidence']}")
            st.write(item["summary"])
            st.markdown("**主要论据：** " + "；".join(item["arguments"]))
            st.markdown("**关注指标：** " + "、".join(item["indicators"]))
            st.link_button("查看原始来源", item["source_url"])
    with st.expander("知识库覆盖情况"):
        views = load_knowledge()
        st.write(f"当前收录 {len(views)} 位人物/观点。")
        st.dataframe(pd.DataFrame(views)[["person", "role", "date", "stance", "source_type"]], hide_index=True, width="stretch")


def render_ai_bubble_page(show_header=True, view="all"):
    diagnosis = unified_ai_bubble_diagnosis()
    analogs, analog_df = all_bubble_series()
    if show_header:
        section_header(
            "AI CYCLE / HISTORY",
            "AI 泡沫知识库",
            f"诊断日期 {diagnosis['as_of_date']}｜历史重建、当前指标与人物观点分层展示",
        )
    m1, m2, m3 = st.columns([2, 1, 1])
    m1.metric("当前阶段", diagnosis["stage"])
    m2.metric("泡沫热度", f"{diagnosis['stage_score']}/100")
    m3.metric("置信度", diagnosis["confidence"])
    st.success("**总判断：** " + diagnosis["conclusion"])

    if view == "monitor":
        _render_ai_timeline(diagnosis, analog_df)
        return
    if view == "history":
        _render_history_map(analogs, analog_df, diagnosis)
        return
    if view == "dalio":
        _render_dalio(diagnosis)
        st.divider()
        _render_views()
        return

    ai_tab, history_tab, dalio_tab, views_tab = st.tabs(["AI长期轨迹", "历史泡沫对比", "Dalio诊断", "人物观点"])
    with ai_tab:
        _render_ai_timeline(diagnosis, analog_df)
    with history_tab:
        _render_history_map(analogs, analog_df, diagnosis)
    with dalio_tab:
        _render_dalio(diagnosis)
    with views_tab:
        _render_views()
