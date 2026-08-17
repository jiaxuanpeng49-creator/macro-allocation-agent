"""Macro Portal：按决策、情报、研究重新分层的 Streamlit 应用。"""

import streamlit as st

from agent_ui import render_agent_experience
from backtest_ui import render_backtest_page
from bubble_ui import render_ai_bubble_page
from dashboard_ui import render_investment_dashboard
from news_ui import render_news_intelligence_page
from ui_theme import apply_theme, render_agent_orb, render_brand_bar, section_header


st.set_page_config(
    page_title="宏观资产配置 Agent",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()
render_brand_bar()
render_agent_orb()

dashboard_page, intelligence_page, research_page = st.tabs(
    ["投资驾驶舱", "情报中心", "研究与验证"],
    key="primary_navigation",
    on_change="rerun",
)

if dashboard_page.open:
    with dashboard_page:
        render_investment_dashboard()

if intelligence_page.open:
    with intelligence_page:
        section_header(
            "INTELLIGENCE CENTER",
            "情报中心",
            "当天新闻、历史归档与 AI 连续监测分别展示，避免把不同时间尺度混在同一页面。",
        )
        today_tab, archive_tab, ai_monitor_tab = st.tabs(
            ["今日情报", "历史归档", "AI 连续监测"],
            key="intelligence_navigation",
            on_change="rerun",
        )
        if today_tab.open:
            with today_tab:
                render_news_intelligence_page(show_header=False, mode="today")
        if archive_tab.open:
            with archive_tab:
                render_news_intelligence_page(show_header=False, mode="archive")
        if ai_monitor_tab.open:
            with ai_monitor_tab:
                render_ai_bubble_page(show_header=False, view="monitor")

if research_page.open:
    with research_page:
        section_header(
            "RESEARCH & VALIDATION",
            "研究与验证",
            "长期回测回答策略是否有效，历史泡沫回答今天走到哪里，Dalio 模型回答当前阶段。",
        )
        backtest_tab, bubble_history_tab, dalio_tab = st.tabs(
            ["30 年回测", "历史泡沫", "Dalio 模型"],
            key="research_navigation",
            on_change="rerun",
        )
        if backtest_tab.open:
            with backtest_tab:
                render_backtest_page()
        if bubble_history_tab.open:
            with bubble_history_tab:
                render_ai_bubble_page(show_header=False, view="history")
        if dalio_tab.open:
            with dalio_tab:
                render_ai_bubble_page(show_header=False, view="dalio")

render_agent_experience()
