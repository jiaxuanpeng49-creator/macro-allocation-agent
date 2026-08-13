"""可下载报告生成器；保持与 Streamlit UI 解耦以便测试。"""

from html import escape
from io import BytesIO
from os import environ
from pathlib import Path


def _register_pdf_font(pdfmetrics, UnicodeCIDFont, TTFont):
    """优先嵌入可移植中文字体；系统字体只作为本地开发兜底。"""
    configured = environ.get("MACRO_PDF_FONT")
    local_candidates = [
        configured,
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for candidate in local_candidates:
        if candidate and Path(candidate).is_file():
            pdfmetrics.registerFont(TTFont("MacroCN", candidate))
            return "MacroCN"

    try:
        from justmytype import get_default_registry

        registry = get_default_registry()
        for family in ("Noto Sans SC", "Noto Sans CJK SC", "Noto Sans JP"):
            match = registry.find_font(family, weight=400)
            if match and Path(match.path).is_file():
                pdfmetrics.registerFont(TTFont("MacroCN", str(match.path)))
                return "MacroCN"
    except Exception:
        pass

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    return "STSong-Light"


def build_conversation_pdf(messages):
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    font_name = _register_pdf_font(pdfmetrics, UnicodeCIDFont, TTFont)
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Macro Portal Agent 对话报告",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleCN",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=21,
        leading=28,
        textColor=HexColor("#0A1538"),
    )
    meta = ParagraphStyle(
        "MetaCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=9,
        leading=14,
        textColor=HexColor("#5F6B8B"),
        alignment=TA_CENTER,
    )
    user_style = ParagraphStyle(
        "UserCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=17,
        textColor=HexColor("#173B98"),
        leftIndent=10 * mm,
        spaceBefore=8,
        spaceAfter=5,
    )
    agent_style = ParagraphStyle(
        "AgentCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=17,
        textColor=HexColor("#0A1538"),
        rightIndent=6 * mm,
        spaceBefore=5,
        spaceAfter=10,
    )
    footer = ParagraphStyle(
        "FooterCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=9.5,
        leading=15,
        textColor=HexColor("#4266E8"),
        alignment=TA_CENTER,
        spaceBefore=14,
    )
    story = [
        Paragraph("Macro Portal Agent 对话报告", title),
        Paragraph("宏观、个人风险、历史验证与每日情报的综合研究记录", meta),
        Spacer(1, 8 * mm),
    ]
    for item in messages:
        label = "你" if item["role"] == "user" else "Agent"
        style = user_style if item["role"] == "user" else agent_style
        content = escape(str(item["content"])).replace("\n", "<br/>")
        story.append(Paragraph(f"<b>{label}</b><br/>{content}", style))
    story.extend(
        [
            Spacer(1, 8 * mm),
            Paragraph(
                "持续获得宏观判断与个性化资产配置建议，欢迎访问 "
                "https://macro-allocation-agent.onrender.com",
                footer,
            ),
            Paragraph("研究与教学用途，不构成投资建议。", meta),
        ]
    )
    document.build(story)
    return output.getvalue()
