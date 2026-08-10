"""Streamlit 视觉系统：深色、可信、数据密集型金融仪表板。"""

import streamlit as st


COLORS = {
    "background": "#0F172A",
    "surface": "#101A34",
    "surface_raised": "#17233F",
    "primary": "#3B82F6",
    "primary_dark": "#1E40AF",
    "accent": "#10B981",
    "warning": "#F59E0B",
    "danger": "#F87171",
    "text": "#F8FAFC",
    "muted": "#A7B2C5",
    "border": "rgba(255,255,255,0.10)",
    "grid": "rgba(148,163,184,0.18)",
}


def apply_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@400;500;600;700&display=swap');

        :root {
          --fin-bg: #0F172A;
          --fin-surface: #101A34;
          --fin-surface-raised: #17233F;
          --fin-primary: #3B82F6;
          --fin-primary-dark: #1E40AF;
          --fin-accent: #10B981;
          --fin-text: #F8FAFC;
          --fin-muted: #A7B2C5;
          --fin-border: rgba(255,255,255,.10);
          --fin-shadow: 0 12px 30px rgba(0,0,0,.20);
        }

        html, body, [class*="css"] { font-family: 'Fira Sans', system-ui, sans-serif; }
        .stApp {
          background:
            radial-gradient(circle at 85% 0%, rgba(30,64,175,.20), transparent 28rem),
            var(--fin-bg);
          color: var(--fin-text);
        }
        .block-container { max-width: 1280px; padding-top: 1.5rem; padding-bottom: 4rem; }
        h1, h2, h3 { color: var(--fin-text); letter-spacing: -.02em; }
        h1, h2 { font-family: 'Fira Code', ui-monospace, monospace; }
        p, label, .stCaption { color: var(--fin-muted); line-height: 1.6; }
        code, [data-testid="stMetricValue"] { font-family: 'Fira Code', ui-monospace, monospace; font-variant-numeric: tabular-nums; }

        .fin-hero {
          border: 1px solid var(--fin-border);
          background: linear-gradient(135deg, rgba(30,64,175,.38), rgba(16,26,52,.96) 58%);
          border-radius: 18px;
          padding: 28px 30px;
          box-shadow: var(--fin-shadow);
          margin-bottom: 22px;
        }
        .fin-eyebrow { color: #93C5FD; font: 500 12px/1.4 'Fira Code', monospace; letter-spacing: .12em; text-transform: uppercase; }
        .fin-hero h1 { margin: 8px 0 6px; font-size: clamp(1.65rem, 3vw, 2.55rem); }
        .fin-hero p { max-width: 760px; margin: 0; color: #CBD5E1; }
        .fin-status-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
        .fin-badge { display: inline-flex; align-items: center; min-height: 30px; padding: 5px 10px; border: 1px solid var(--fin-border); border-radius: 999px; color: #DCE8FF; background: rgba(15,23,42,.45); font-size: 13px; }
        .fin-badge strong { color: #6EE7B7; margin-left: 5px; }

        .fin-section { margin: 18px 0 12px; }
        .fin-section-index { color: #60A5FA; font: 500 12px/1.4 'Fira Code', monospace; letter-spacing: .10em; }
        .fin-section-title { color: var(--fin-text); font: 600 22px/1.35 'Fira Code', monospace; margin-top: 4px; }
        .fin-section-copy { color: var(--fin-muted); max-width: 820px; margin-top: 5px; }

        [data-testid="stMetric"] {
          background: linear-gradient(180deg, rgba(23,35,63,.96), rgba(16,26,52,.96));
          border: 1px solid var(--fin-border);
          border-radius: 14px;
          padding: 16px 18px;
          box-shadow: 0 6px 18px rgba(0,0,0,.12);
          min-height: 112px;
        }
        [data-testid="stMetricLabel"] { color: var(--fin-muted); font-weight: 500; }
        [data-testid="stMetricValue"] { color: var(--fin-text); font-size: clamp(1.3rem, 2vw, 1.85rem); }
        [data-testid="stMetricDelta"] { font-weight: 600; }

        .stTabs [data-baseweb="tab-list"] {
          gap: 6px; padding: 5px; background: rgba(16,26,52,.90);
          border: 1px solid var(--fin-border); border-radius: 12px;
        }
        .stTabs [data-baseweb="tab"] {
          min-height: 44px; padding: 8px 16px; border-radius: 8px;
          color: var(--fin-muted); transition: background-color 180ms ease, color 180ms ease;
        }
        .stTabs [aria-selected="true"] { background: #1E40AF; color: #FFFFFF; }
        .stTabs [data-baseweb="tab-highlight"] { display: none; }

        [data-testid="stForm"], [data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"] {
          background: rgba(16,26,52,.88); border: 1px solid var(--fin-border);
          border-radius: 14px; box-shadow: 0 8px 22px rgba(0,0,0,.13);
        }
        [data-testid="stForm"] { padding: 20px; }
        [data-testid="stExpander"] { overflow: hidden; }

        .stButton > button, [data-testid="stFormSubmitButton"] button, .stLinkButton > a {
          min-height: 44px; border-radius: 9px; font-weight: 600; cursor: pointer;
          transition: background-color 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
        }
        [data-testid="stFormSubmitButton"] button[kind="primary"], .stButton button[kind="primary"] {
          background: #059669; border-color: #10B981; color: white;
        }
        [data-testid="stFormSubmitButton"] button[kind="primary"]:hover, .stButton button[kind="primary"]:hover {
          background: #047857; border-color: #34D399; box-shadow: 0 0 0 3px rgba(16,185,129,.20);
        }
        button:focus-visible, input:focus-visible, [role="tab"]:focus-visible, a:focus-visible {
          outline: 3px solid rgba(96,165,250,.75) !important; outline-offset: 2px;
        }
        input, textarea, [data-baseweb="select"] > div {
          min-height: 44px; border-radius: 9px !important; background: #0B1328 !important;
          border-color: rgba(148,163,184,.28) !important; color: var(--fin-text) !important;
        }
        input:focus, textarea:focus { border-color: #60A5FA !important; box-shadow: 0 0 0 3px rgba(59,130,246,.18) !important; }

        [data-testid="stAlert"] { border-radius: 12px; border: 1px solid var(--fin-border); }
        [data-testid="stDataFrame"] { border: 1px solid var(--fin-border); border-radius: 12px; overflow: hidden; }
        [data-testid="stPlotlyChart"] { background: rgba(16,26,52,.72); border: 1px solid var(--fin-border); border-radius: 14px; padding: 8px; }
        hr { border-color: var(--fin-border); margin: 28px 0; }

        @media (max-width: 768px) {
          .block-container { padding: 1rem .85rem 3rem; }
          .fin-hero { padding: 22px 18px; border-radius: 14px; }
          .stTabs [data-baseweb="tab-list"] {
            gap: 2px; overflow-x: auto; flex-wrap: nowrap; scrollbar-width: none;
          }
          .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
          .stTabs [data-baseweb="tab"] {
            flex: 0 0 auto; min-width: auto !important; padding-inline: 10px !important;
            white-space: nowrap; font-size: 12px; justify-content: center;
          }
          .stTabs [data-baseweb="tab"] p { font-size: 12px !important; }
          [data-testid="stMetric"] { min-height: 96px; padding: 13px 14px; }
        }
        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header():
    st.markdown(
        """
        <header class="fin-hero">
          <div class="fin-eyebrow">MACRO × PERSONAL RISK × AI CYCLE</div>
          <h1>宏观资产配置 Agent</h1>
          <p>把当前经济周期、个人风险边界与长期历史验证放进同一个决策框架。先保护财务安全，再讨论收益。</p>
          <div class="fin-status-row">
            <span class="fin-badge">数据频率<strong>月度</strong></span>
            <span class="fin-badge">历史区间<strong>1995–2025</strong></span>
            <span class="fin-badge">AI泡沫诊断<strong>76 / 100</strong></span>
            <span class="fin-badge">用途<strong>研究与教学</strong></span>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def section_header(index, title, copy):
    st.markdown(
        f"""
        <div class="fin-section">
          <div class="fin-section-index">{index}</div>
          <div class="fin-section-title">{title}</div>
          <div class="fin-section-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plotly(figure, title=None, height=None):
    figure.update_layout(
        title=title,
        font={"family": "Fira Sans, Arial", "color": COLORS["text"]},
        title_font={"family": "Fira Code, monospace", "size": 17, "color": COLORS["text"]},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=["#3B82F6", "#10B981", "#F59E0B", "#A78BFA", "#38BDF8", "#F87171"],
        hoverlabel={"bgcolor": COLORS["surface_raised"], "font_color": COLORS["text"]},
        margin={"l": 48, "r": 24, "t": 58, "b": 48},
        height=height,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    figure.update_xaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"], title_font_color=COLORS["muted"], tickfont_color=COLORS["muted"])
    figure.update_yaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"], title_font_color=COLORS["muted"], tickfont_color=COLORS["muted"])
    return figure
