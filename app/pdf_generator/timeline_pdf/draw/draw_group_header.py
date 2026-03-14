from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from app.pdf_generator.base import get_font
from app.pdf_generator.color_constants import (
    COLOR_BORDER_DARK,
    COLOR_TEXT_SECONDARY,
)
from app.pdf_generator.timeline_pdf.layout_constants import (
    PAGE_PADDING_LEFT,
)

# -------------------------
# FIGMA CONSTANTS
# -------------------------

GROUP_BOX_WIDTH = 525
GROUP_BOX_HEIGHT = 26

GROUP_PADDING_LEFT = 12
GROUP_PADDING_RIGHT = 12
GROUP_PADDING_TOP = 8
GROUP_PADDING_BOTTOM = 8

# 세로선 컨테이너 너비
TIMELINE_VERTICAL_LINE_CONTAINER_WIDTH = 22

FONT_MEDIUM = get_font("medium")


def draw_group_header(
    c: Canvas,
    start_y: float,
    date_text: str,
    total_count: int,
    evidence_number: str,
):
    # -------------------------
    # BOX POSITION
    # -------------------------

    x = PAGE_PADDING_LEFT + TIMELINE_VERTICAL_LINE_CONTAINER_WIDTH
    y = start_y - GROUP_BOX_HEIGHT

    # -------------------------
    # BOX DRAW
    # -------------------------

    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColor(COLOR_BORDER_DARK)
    c.setLineWidth(1)

    c.rect(
        x,
        y,
        GROUP_BOX_WIDTH,
        GROUP_BOX_HEIGHT,
        fill=1,
        stroke=1,
    )

    # -------------------------
    # TEXT BASELINE
    # -------------------------

    text_y = start_y - GROUP_PADDING_TOP - 7.5

    # -------------------------
    # DATE TEXT
    # -------------------------

    c.setFont(FONT_MEDIUM, 7.5)
    c.setFillColorRGB(1, 1, 1)

    date_x = x + GROUP_PADDING_LEFT

    c.drawString(
        date_x,
        text_y,
        date_text,
    )

    # -------------------------
    # TOTAL COUNT TEXT
    # -------------------------

    total_text = f"총 {total_count}개"

    total_x = date_x + stringWidth(date_text, FONT_MEDIUM, 7.5) + 8

    c.setFont(FONT_MEDIUM, 7)
    c.setFillColor(COLOR_TEXT_SECONDARY)

    c.drawString(
        total_x,
        text_y,
        total_text,
    )

    # -------------------------
    # EVIDENCE NUMBER TEXT
    # -------------------------

    evidence_text = f"증거 번호 {evidence_number}"

    text_width = stringWidth(evidence_text, FONT_MEDIUM, 7)

    evidence_x = x + GROUP_BOX_WIDTH - GROUP_PADDING_RIGHT - text_width

    c.drawString(
        evidence_x,
        text_y,
        evidence_text,
    )

    # -------------------------
    # CENTER Y (timeline circle)
    # -------------------------

    center_y = y + (GROUP_BOX_HEIGHT / 2)
    end_y = y

    return center_y, end_y
