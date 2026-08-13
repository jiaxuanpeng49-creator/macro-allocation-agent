"""Streamlit 视觉系统：虹彩浅色、Liquid Glass 与苹果式滚动叙事。"""

from html import escape

import streamlit as st


COLORS = {
    "background": "#F4F6FF",
    "surface": "#FFFFFF",
    "surface_raised": "#F8F9FF",
    "primary": "#4266E8",
    "primary_dark": "#173B98",
    "accent": "#775CF0",
    "warning": "#B7791F",
    "danger": "#C34F67",
    "text": "#0A1538",
    "muted": "#5F6B8B",
    "border": "rgba(78,101,181,0.16)",
    "grid": "rgba(88,107,178,0.13)",
}


def apply_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Space+Grotesk:wght@400;500;600&display=swap');

        :root {
          --fin-bg: #F4F6FF;
          --fin-bg-soft: #EEF2FF;
          --fin-surface: rgba(255,255,255,.58);
          --fin-surface-strong: rgba(255,255,255,.78);
          --fin-primary: #4266E8;
          --fin-primary-dark: #173B98;
          --fin-accent: #775CF0;
          --fin-pink: #D98BD1;
          --fin-cyan: #82D4F8;
          --fin-text: #0A1538;
          --fin-muted: #5F6B8B;
          --fin-border: rgba(78,101,181,.16);
          --fin-glass-border: rgba(255,255,255,.88);
          --fin-shadow: 0 20px 55px rgba(67,83,156,.12);
          --fin-shadow-soft: 0 10px 28px rgba(67,83,156,.09);
          --fin-ease: cubic-bezier(.16,1,.3,1);
        }

        html { scroll-behavior: smooth; }
        html, body, [class*="css"] { font-family: 'DM Sans', system-ui, sans-serif; }
        .stApp {
          color: var(--fin-text);
          background:
            radial-gradient(circle at 74% 6%, rgba(130,156,255,.34), transparent 28rem),
            radial-gradient(circle at 102% 28%, rgba(120,169,255,.24), transparent 36rem),
            radial-gradient(circle at 2% 64%, rgba(228,190,255,.25), transparent 32rem),
            linear-gradient(145deg, #FCFDFF 0%, #F5F5FF 42%, #EEF2FF 72%, #E9EEFF 100%);
          background-attachment: fixed;
        }
        .stApp::before {
          content: "";
          position: fixed;
          inset: 0;
          z-index: -1;
          pointer-events: none;
          background:
            radial-gradient(circle at 18% 16%, rgba(255,255,255,.92) 0 2px, transparent 3px),
            radial-gradient(circle at 81% 30%, rgba(255,255,255,.88) 0 1.5px, transparent 2.5px),
            radial-gradient(circle at 67% 58%, rgba(255,255,255,.82) 0 1px, transparent 2px);
          background-size: 370px 370px, 460px 460px, 290px 290px;
        }
        .block-container { max-width: 1440px; padding-top: 1rem; padding-bottom: 6rem; }
        h1, h2, h3, h4 { color: var(--fin-text); letter-spacing: -.035em; }
        h1, h2, h3, [data-testid="stMetricValue"] { font-family: 'Space Grotesk', system-ui, sans-serif; }
        p, label, .stCaption { color: var(--fin-muted); line-height: 1.62; }
        code, [data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }

        /* 品牌栏 */
        .fin-brandbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          min-height: 58px;
          margin-bottom: 8px;
          padding: 8px 12px;
        }
        .fin-brand { display: inline-flex; align-items: center; gap: 11px; color: var(--fin-text); }
        .fin-brand-mark {
          position: relative;
          width: 31px;
          height: 31px;
          transform: rotate(30deg);
          border-radius: 9px;
          background: conic-gradient(from 0deg, #4369F2, #9A7CFF, #83D5FF, #4369F2);
          box-shadow: 0 8px 20px rgba(74,88,229,.25);
        }
        .fin-brand-mark::after {
          content: "";
          position: absolute;
          inset: 7px;
          border-radius: 4px;
          background: rgba(249,250,255,.95);
        }
        .fin-brand-name { font: 600 19px/1.2 'Space Grotesk', sans-serif; letter-spacing: -.03em; }
        .fin-live {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          min-height: 34px;
          padding: 6px 11px;
          color: #354678;
          background: rgba(255,255,255,.48);
          border: 1px solid rgba(255,255,255,.78);
          border-radius: 999px;
          box-shadow: 0 8px 22px rgba(76,91,169,.08);
          backdrop-filter: blur(18px) saturate(150%);
          -webkit-backdrop-filter: blur(18px) saturate(150%);
        }
        .fin-live-dot { width: 8px; height: 8px; border-radius: 50%; background: #4C7CF3; box-shadow: 0 0 0 4px rgba(76,124,243,.12); }

        /* 可点击的悬浮导航，模拟 macOS Tahoe/27 的浮动工具栏 */
        .stTabs [data-baseweb="tab-list"] {
          position: sticky;
          top: .55rem;
          z-index: 999;
          gap: 5px;
          width: fit-content;
          max-width: 100%;
          margin: 0 auto 12px;
          padding: 5px;
          overflow-x: auto;
          flex-wrap: nowrap;
          background:
            linear-gradient(115deg, rgba(255,255,255,.76), rgba(246,247,255,.48)),
            radial-gradient(circle at 20% 0%, rgba(255,255,255,.88), transparent 42%);
          border: 1px solid rgba(255,255,255,.90);
          border-radius: 999px;
          box-shadow: 0 16px 38px rgba(71,84,156,.13), inset 0 1px 0 rgba(255,255,255,.94);
          backdrop-filter: blur(28px) saturate(170%);
          -webkit-backdrop-filter: blur(28px) saturate(170%);
          scrollbar-width: none;
        }
        .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
        .stTabs [data-baseweb="tab"] {
          flex: 0 0 auto;
          min-height: 43px;
          padding: 8px 16px;
          color: #37456B;
          border-radius: 999px;
          transition: color 220ms var(--fin-ease), background 220ms var(--fin-ease), box-shadow 220ms var(--fin-ease), transform 220ms var(--fin-ease);
        }
        .stTabs [data-baseweb="tab"]:hover { color: var(--fin-primary); background: rgba(255,255,255,.52); transform: translateY(-1px); }
        .stTabs [aria-selected="true"] {
          color: var(--fin-primary);
          background: rgba(255,255,255,.86);
          box-shadow: 0 8px 22px rgba(65,81,161,.10), inset 0 0 0 1px rgba(255,255,255,.92);
        }
        .stTabs [data-baseweb="tab-highlight"] { display: none; }

        /* 大幅 Hero */
        .fin-hero {
          position: relative;
          display: grid;
          grid-template-columns: minmax(0,.95fr) minmax(320px,1.05fr);
          align-items: center;
          min-height: 465px;
          margin: 10px 0 24px;
          padding: 42px 34px 28px;
          overflow: hidden;
          isolation: isolate;
        }
        .fin-hero::before {
          content: "";
          position: absolute;
          z-index: -2;
          inset: 0;
          background:
            radial-gradient(circle at 76% 36%, rgba(123,146,255,.26), transparent 31%),
            radial-gradient(circle at 93% 58%, rgba(111,167,255,.20), transparent 34%);
        }
        .fin-hero-copy { position: relative; z-index: 3; max-width: 620px; }
        .fin-eyebrow { color: #5265A6; font: 500 12px/1.4 'Space Grotesk', sans-serif; letter-spacing: .19em; text-transform: uppercase; }
        .fin-hero h1 { margin: 16px 0 0; font-size: clamp(2.8rem, 6.2vw, 5.6rem); line-height: .98; letter-spacing: -.065em; }
        .fin-gradient-word {
          display: block;
          color: transparent;
          background: linear-gradient(90deg, #3077F5 0%, #685BE6 48%, #B27BEE 100%);
          -webkit-background-clip: text;
          background-clip: text;
        }
        .fin-hero p { max-width: 560px; margin: 19px 0 0; color: #51607F; font-size: 1.02rem; }
        .fin-status-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 21px; }
        .fin-badge {
          display: inline-flex;
          align-items: center;
          min-height: 34px;
          padding: 6px 10px;
          color: #40517A;
          background: rgba(255,255,255,.43);
          border: 1px solid rgba(81,103,180,.13);
          border-radius: 999px;
          box-shadow: inset 0 1px 0 rgba(255,255,255,.72);
          backdrop-filter: blur(14px) saturate(140%);
          -webkit-backdrop-filter: blur(14px) saturate(140%);
        }
        .fin-badge::before { content: ""; width: 6px; height: 6px; margin-right: 7px; border-radius: 50%; background: linear-gradient(145deg, var(--fin-primary), var(--fin-accent)); }
        .fin-badge strong { color: var(--fin-primary); margin-left: 5px; }
        .fin-orbit-stage { position: relative; min-height: 390px; }
        .fin-orbit {
          position: absolute;
          left: 1%;
          top: 18%;
          width: 96%;
          height: 66%;
          border: 1px solid rgba(255,255,255,.66);
          border-radius: 50%;
          transform: rotate(11deg);
          box-shadow: 0 0 28px rgba(255,255,255,.46), inset 0 0 18px rgba(151,163,255,.18);
        }
        .fin-sphere {
          position: absolute;
          display: grid;
          place-items: center;
          border-radius: 50%;
          background:
            radial-gradient(circle at 31% 24%, rgba(255,255,255,.98) 0 7%, rgba(255,255,255,.58) 15%, transparent 31%),
            radial-gradient(circle at 70% 72%, rgba(255,182,241,.43), transparent 35%),
            radial-gradient(circle at 38% 65%, rgba(119,205,255,.39), transparent 48%),
            linear-gradient(145deg, rgba(255,255,255,.70), rgba(111,112,236,.25) 46%, rgba(255,255,255,.57));
          border: 1px solid rgba(255,255,255,.86);
          box-shadow:
            inset 15px 18px 28px rgba(255,255,255,.78),
            inset -20px -18px 38px rgba(106,102,221,.22),
            0 22px 52px rgba(90,93,190,.18),
            0 0 0 2px rgba(255,255,255,.18);
          backdrop-filter: blur(6px) saturate(155%);
          -webkit-backdrop-filter: blur(6px) saturate(155%);
        }
        .fin-sphere::before { content: ""; position: absolute; inset: 7%; border: 1px solid rgba(255,255,255,.68); border-radius: 50%; box-shadow: inset 0 0 38px rgba(255,255,255,.34); }
        .fin-sphere-main { top: 2%; left: 18%; width: min(32vw, 350px); height: min(32vw, 350px); min-width: 280px; min-height: 280px; }
        .fin-sphere-label {
          position: relative;
          z-index: 1;
          color: rgba(255,255,255,.68);
          font: 600 clamp(3.4rem, 7vw, 6.7rem)/1 'Space Grotesk', sans-serif;
          letter-spacing: -.07em;
          text-shadow: 0 3px 3px rgba(255,255,255,.86), 0 8px 22px rgba(79,79,182,.22);
          -webkit-text-stroke: 1px rgba(255,255,255,.76);
        }
        .fin-sphere-small { width: 66px; height: 66px; }
        .fin-s1 { top: 5%; left: 3%; }
        .fin-s2 { top: 22%; right: 0; width: 82px; height: 82px; }
        .fin-s3 { bottom: 3%; left: 10%; width: 51px; height: 51px; }
        .fin-s4 { bottom: 3%; right: 9%; width: 59px; height: 59px; }

        /* 内容区和 Liquid Glass 组件 */
        .fin-section { margin: 24px 0 14px; }
        .fin-section-index { color: var(--fin-primary); font: 500 12px/1.4 'Space Grotesk', sans-serif; letter-spacing: .13em; text-transform: uppercase; }
        .fin-section-title { color: var(--fin-text); font: 600 24px/1.3 'Space Grotesk', sans-serif; margin-top: 5px; letter-spacing: -.035em; }
        .fin-section-copy { color: var(--fin-muted); max-width: 840px; margin-top: 5px; }

        [data-testid="stMetric"],
        [data-testid="stForm"],
        [data-testid="stExpander"],
        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stPlotlyChart"] {
          position: relative;
          overflow: hidden;
          background:
            linear-gradient(135deg, rgba(255,255,255,.72), rgba(246,247,255,.50)),
            radial-gradient(circle at 14% 0%, rgba(255,255,255,.96), transparent 36%);
          border: 1px solid var(--fin-glass-border);
          box-shadow: var(--fin-shadow-soft), inset 0 1px 0 rgba(255,255,255,.94);
          backdrop-filter: blur(22px) saturate(155%);
          -webkit-backdrop-filter: blur(22px) saturate(155%);
        }
        [data-testid="stMetric"]::before,
        [data-testid="stForm"]::before,
        [data-testid="stVerticalBlockBorderWrapper"]::before {
          content: "";
          position: absolute;
          inset: 0;
          z-index: 0;
          pointer-events: none;
          background: linear-gradient(112deg, rgba(255,255,255,.52), transparent 30%, transparent 66%, rgba(150,172,255,.10));
        }
        [data-testid="stMetric"] > *, [data-testid="stForm"] > *, [data-testid="stVerticalBlockBorderWrapper"] > * { position: relative; z-index: 1; }
        [data-testid="stMetric"] {
          min-height: 116px;
          padding: 17px 18px;
          border-radius: 18px;
          transition: transform 320ms var(--fin-ease), box-shadow 320ms var(--fin-ease), border-color 320ms var(--fin-ease);
        }
        [data-testid="stMetric"]:hover { transform: translateY(-4px) scale(1.008); border-color: rgba(255,255,255,.98); box-shadow: 0 18px 40px rgba(65,81,161,.14), inset 0 1px 0 #fff; }
        [data-testid="stMetricLabel"] { color: var(--fin-muted); font-weight: 500; }
        [data-testid="stMetricValue"] { color: var(--fin-text); font-size: clamp(1.3rem, 2vw, 1.9rem); }
        [data-testid="stMetricDelta"] { font-weight: 600; }
        [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] { padding: 20px; border-radius: 22px; }
        [data-testid="stExpander"] { border-radius: 17px; }
        [data-testid="stPlotlyChart"] { padding: 9px; border-radius: 20px; }

        .stButton > button, [data-testid="stFormSubmitButton"] button, .stLinkButton > a, .stDownloadButton > button {
          min-height: 44px;
          border-radius: 999px;
          font-weight: 600;
          cursor: pointer;
          color: #22335F;
          background: rgba(255,255,255,.64);
          border: 1px solid rgba(255,255,255,.92);
          box-shadow: 0 9px 24px rgba(71,86,163,.10), inset 0 1px 0 rgba(255,255,255,.96);
          backdrop-filter: blur(18px) saturate(150%);
          -webkit-backdrop-filter: blur(18px) saturate(150%);
          transition: transform 220ms var(--fin-ease), box-shadow 220ms var(--fin-ease), background 220ms var(--fin-ease);
        }
        .stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover, .stLinkButton > a:hover { transform: translateY(-2px); background: rgba(255,255,255,.88); box-shadow: 0 14px 30px rgba(71,86,163,.14); }
        [data-testid="stFormSubmitButton"] button[kind="primary"], .stButton button[kind="primary"] {
          color: #FFFFFF;
          background: linear-gradient(135deg, #183A91, #0A1538);
          border-color: rgba(9,24,65,.92);
          box-shadow: 0 13px 28px rgba(10,21,56,.20), inset 0 1px 0 rgba(255,255,255,.20);
        }
        [data-testid="stFormSubmitButton"] button[kind="primary"]:hover, .stButton button[kind="primary"]:hover { background: linear-gradient(135deg, #244BAD, #0A1538); }
        button:focus-visible, input:focus-visible, [role="tab"]:focus-visible, a:focus-visible { outline: 3px solid rgba(66,102,232,.52) !important; outline-offset: 3px; }

        input, textarea, [data-baseweb="select"] > div {
          min-height: 44px;
          color: var(--fin-text) !important;
          background: rgba(255,255,255,.58) !important;
          border-color: rgba(80,101,177,.19) !important;
          border-radius: 14px !important;
          box-shadow: inset 0 1px 0 rgba(255,255,255,.88);
        }
        input:focus, textarea:focus { border-color: var(--fin-primary) !important; box-shadow: 0 0 0 3px rgba(66,102,232,.13) !important; }
        [data-baseweb="popover"], [data-baseweb="menu"] { backdrop-filter: blur(24px) saturate(150%); -webkit-backdrop-filter: blur(24px) saturate(150%); }
        [data-testid="stSlider"] [role="slider"] { background: var(--fin-primary); border-color: #ffffff; box-shadow: 0 4px 12px rgba(66,102,232,.22); }
        [data-testid="stAlert"] { border-radius: 17px; border: 1px solid rgba(255,255,255,.85); box-shadow: 0 10px 26px rgba(70,84,156,.08); }
        [data-testid="stDataFrame"] { border: 1px solid rgba(255,255,255,.88); border-radius: 18px; overflow: hidden; box-shadow: var(--fin-shadow-soft); }
        hr { border-color: var(--fin-border); margin: 30px 0; }

        /* 内层 tabs 继续用较轻的玻璃分段控制器，不和主导航竞争 */
        .stTabs .stTabs [data-baseweb="tab-list"] {
          position: static;
          width: 100%;
          justify-content: flex-start;
          margin: 4px 0 14px;
          background: rgba(255,255,255,.40);
          box-shadow: inset 0 0 0 1px rgba(255,255,255,.62);
        }

        /* 苹果产品页式进入视野：支持时启用，不支持时保持完整可见 */
        @supports (animation-timeline: view()) {
          .fin-reveal,
          [data-testid="stMetric"],
          [data-testid="stForm"],
          [data-testid="stVerticalBlockBorderWrapper"],
          [data-testid="stPlotlyChart"],
          [data-testid="stDataFrame"] {
            animation: fin-enter linear both;
            animation-timeline: view();
            animation-range: entry 3% cover 26%;
          }
          .fin-orbit-stage {
            animation: fin-orbit-scroll linear both;
            animation-timeline: view();
            animation-range: entry 0% exit 100%;
          }
        }
        @keyframes fin-enter {
          from { opacity: .18; transform: translateY(34px) scale(.975); filter: blur(6px); }
          to { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        }
        @keyframes fin-orbit-scroll {
          0% { transform: translateY(18px) scale(.95); }
          52% { transform: translateY(0) scale(1); }
          100% { transform: translateY(-26px) scale(1.035); }
        }

        @media (max-width: 900px) {
          .block-container { padding-inline: 1rem; }
          .fin-hero { grid-template-columns: minmax(0,1fr) 340px; padding-inline: 22px; }
          .fin-sphere-main { left: 8%; width: 300px; height: 300px; min-width: 0; min-height: 0; }
          .stTabs [data-baseweb="tab"] { padding-inline: 12px; }
        }
        @media (max-width: 680px) {
          .block-container { padding: .5rem .75rem 4rem; }
          .fin-brandbar { padding-inline: 4px; }
          .fin-live span:last-child { display: none; }
          .fin-hero { grid-template-columns: 1fr; min-height: auto; padding: 34px 10px 10px; }
          .fin-hero h1 { font-size: clamp(2.6rem, 15vw, 4.25rem); }
          .fin-orbit-stage { min-height: 310px; }
          .fin-sphere-main { left: 50%; transform: translateX(-50%); width: 270px; height: 270px; }
          .fin-s1 { left: 1%; } .fin-s2 { right: 1%; }
          .stTabs [data-baseweb="tab-list"] { width: 100%; margin-bottom: 4px; }
          .stTabs [data-baseweb="tab"] { padding-inline: 10px; }
          .stTabs [data-baseweb="tab"] p { font-size: 12px !important; white-space: nowrap; }
          [data-testid="stMetric"] { min-height: 98px; padding: 14px; }
          [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] { padding: 15px; border-radius: 18px; }
        }
        @media (prefers-reduced-motion: reduce) {
          html { scroll-behavior: auto; }
          *, *::before, *::after { animation: none !important; transition-duration: .01ms !important; }
        }
        @media (prefers-contrast: more) {
          :root { --fin-surface: rgba(255,255,255,.92); --fin-surface-strong: #FFFFFF; --fin-border: rgba(35,52,105,.30); }
          [data-testid="stMetric"], [data-testid="stForm"], [data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stPlotlyChart"] { background: rgba(255,255,255,.94); backdrop-filter: none; -webkit-backdrop-filter: none; border-color: rgba(35,52,105,.28); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_bar():
    st.markdown(
        """
        <div class="fin-brandbar">
          <div class="fin-brand">
            <span class="fin-brand-mark" aria-hidden="true"></span>
            <span class="fin-brand-name">Macro Portal</span>
          </div>
          <div class="fin-live">
            <span class="fin-live-dot" aria-hidden="true"></span>
            <span>宏观、新闻与模型数据已连接</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_app_header(
    title="宏观资产配置",
    gradient_word="Agent",
    description="把当前经济周期、个人风险边界与长期历史验证放进同一个决策框架。先保护财务安全，再讨论收益。",
    eyebrow="MACRO × PERSONAL RISK × AI CYCLE",
    sphere_label="AI",
    badges=None,
):
    if badges is None:
        badges = [
            ("数据频率", "月度"),
            ("历史区间", "1995–2025"),
            ("AI泡沫诊断", "76 / 100"),
            ("用途", "研究与教学"),
        ]
    badge_html = "".join(
        f'<span class="fin-badge">{escape(label)}<strong>{escape(value)}</strong></span>'
        for label, value in badges
    )
    st.markdown(
        f"""
        <header class="fin-hero fin-reveal">
          <div class="fin-hero-copy">
            <div class="fin-eyebrow">{escape(eyebrow)}</div>
            <h1>{escape(title)}<span class="fin-gradient-word">{escape(gradient_word)}</span></h1>
            <p>{escape(description)}</p>
            <div class="fin-status-row">
              {badge_html}
            </div>
          </div>
          <div class="fin-orbit-stage" aria-hidden="true">
            <div class="fin-orbit"></div>
            <div class="fin-sphere fin-sphere-main"><span class="fin-sphere-label">{escape(sphere_label)}</span></div>
            <div class="fin-sphere fin-sphere-small fin-s1"></div>
            <div class="fin-sphere fin-sphere-small fin-s2"></div>
            <div class="fin-sphere fin-sphere-small fin-s3"></div>
            <div class="fin-sphere fin-sphere-small fin-s4"></div>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def section_header(index, title, copy):
    st.markdown(
        f"""
        <div class="fin-section fin-reveal">
          <div class="fin-section-index">{escape(index)}</div>
          <div class="fin-section-title">{escape(title)}</div>
          <div class="fin-section-copy">{escape(copy)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plotly(figure, title=None, height=None):
    figure.update_layout(
        title=title,
        font={"family": "DM Sans, Arial", "color": COLORS["text"]},
        title_font={"family": "Space Grotesk, Arial", "size": 18, "color": COLORS["text"]},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=["#4266E8", "#775CF0", "#D98BD1", "#5BA8D7", "#C9973B", "#C34F67"],
        hoverlabel={"bgcolor": "rgba(255,255,255,.96)", "font_color": COLORS["text"], "bordercolor": "rgba(78,101,181,.18)"},
        margin={"l": 48, "r": 24, "t": 58, "b": 48},
        height=height,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )
    figure.update_xaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"], title_font_color=COLORS["muted"], tickfont_color=COLORS["muted"])
    figure.update_yaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"], title_font_color=COLORS["muted"], tickfont_color=COLORS["muted"])
    return figure
