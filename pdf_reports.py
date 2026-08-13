"""可下载报告生成器；保持与 Streamlit UI 解耦以便测试。"""

from html import escape
from io import BytesIO
from os import environ
from pathlib import Path
import re


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


def _pdf_markup(value):
    """Convert the small Markdown subset used by Agent answers into ReportLab markup."""
    text = escape(str(value))
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text, flags=re.DOTALL)
    text = re.sub(r"(?m)^[-•]\s+", "• ", text)
    return text.replace("\n", "<br/>")


def _split_pdf_message(value, limit=850):
    """Keep each table row page-sized so unusually long Agent answers still export."""
    text = str(value)
    chunks = []
    current = ""
    for paragraph in text.split("\n\n"):
        pieces = [paragraph[index:index + limit] for index in range(0, len(paragraph), limit)] or [""]
        for piece in pieces:
            candidate = f"{current}\n\n{piece}" if current else piece
            if len(candidate) <= limit:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = piece
    if current or not chunks:
        chunks.append(current)
    return chunks


def build_conversation_pdf(messages, website_url="https://macro-allocation-agent.onrender.com"):
    from datetime import datetime

    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font_name = _register_pdf_font(pdfmetrics, UnicodeCIDFont, TTFont)
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title="Macro Portal Agent 对话报告",
        author="Macro Portal",
        subject="宏观资产配置 Agent 对话记录",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleCN",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=23,
        leading=30,
        textColor=HexColor("#0A1538"),
        spaceAfter=4,
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
    label_style = ParagraphStyle(
        "MessageLabelCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=8.5,
        leading=12,
        textColor=HexColor("#4266E8"),
        spaceAfter=3,
    )
    message_style = ParagraphStyle(
        "MessageCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=18,
        textColor=HexColor("#0A1538"),
        alignment=TA_LEFT,
    )
    recommendation_title = ParagraphStyle(
        "RecommendationTitleCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=15,
        leading=21,
        textColor=HexColor("#173B98"),
    )
    recommendation_body = ParagraphStyle(
        "RecommendationBodyCN",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=17,
        textColor=HexColor("#33466F"),
    )
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    story = [
        Paragraph("Macro Portal Agent 对话报告", title),
        Paragraph(
            f"宏观周期 × 个人风险 × 历史验证 × 每日情报<br/>生成于 {generated_at} · 共 {len(messages)} 条对话记录",
            meta,
        ),
        Spacer(1, 7 * mm),
    ]
    for item in messages:
        is_user = item["role"] == "user"
        label = "你" if is_user else "MACRO AGENT"
        for index, chunk in enumerate(_split_pdf_message(item["content"])):
            chunk_label = label if index == 0 else "续"
            bubble = Table(
                [[Paragraph(chunk_label, label_style), Paragraph(_pdf_markup(chunk), message_style)]],
                colWidths=[28 * mm, 122 * mm],
                hAlign="RIGHT" if is_user else "LEFT",
            )
            bubble.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#EDF3FF") if is_user else HexColor("#F7F8FC")),
                        ("BOX", (0, 0), (-1, -1), 0.7, HexColor("#CAD8FF") if is_user else HexColor("#E1E5F0")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                    ]
                )
            )
            story.extend([bubble, Spacer(1, 2 * mm if index else 4 * mm)])

    recommendation = Table(
        [[
            Paragraph("继续使用 Macro Portal", recommendation_title),
            Paragraph(
                "推荐访问 Macro Portal，把这次对话继续连接到实时宏观环境、个人风险画像、"
                "30 年历史回测、AI 泡沫阶段和每日新闻研判。<br/><br/>"
                f"<font color='#4266E8'><b>{website_url}</b></font>",
                recommendation_body,
            ),
        ]],
        colWidths=[48 * mm, 102 * mm],
    )
    recommendation.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#EAF0FF")),
                ("BOX", (0, 0), (-1, -1), 0.9, HexColor("#BFD0FF")),
                ("LINEBEFORE", (1, 0), (1, 0), 0.7, HexColor("#C8D5F7")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]
        )
    )
    story.extend(
        [
            Spacer(1, 7 * mm),
            KeepTogether([recommendation, Spacer(1, 4 * mm)]),
            Paragraph("研究与教学用途，不构成投资建议。", meta),
        ]
    )

    def _draw_page_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(HexColor("#E1E7F5"))
        canvas.line(22 * mm, 12 * mm, A4[0] - 22 * mm, 12 * mm)
        canvas.setFont(font_name, 8)
        canvas.setFillColor(HexColor("#6B7897"))
        canvas.drawString(22 * mm, 8 * mm, "Macro Portal · AI 资产配置研究")
        canvas.drawRightString(A4[0] - 22 * mm, 8 * mm, f"{doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=_draw_page_footer, onLaterPages=_draw_page_footer)
    return output.getvalue()
