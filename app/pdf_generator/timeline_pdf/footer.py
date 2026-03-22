from reportlab.pdfgen.canvas import Canvas

from app.pdf_generator.base import get_font
from app.pdf_generator.color_constants import (
    COLOR_BORDER_DIVIDER,
    COLOR_TEXT_PRIMARY,
)
from app.pdf_generator.timeline_pdf.layout_constants import (
    FOOTER_BOTTOM_Y,
    PAGE_PADDING_LEFT,
    PAGE_PADDING_RIGHT,
    PAGE_WIDTH,
)

# -------------------------
# Font cache
# -------------------------

FONT_REGULAR = get_font("regular")
FONT_MEDIUM = get_font("medium")


def draw_footer(
    c: Canvas,
    page_number: int,
    case_title: str,
):
    y = FOOTER_BOTTOM_Y
    x = PAGE_PADDING_LEFT

    # -------------------------
    # Left container
    # -------------------------

    label = "사건타임라인"

    # 사건타임라인
    c.setFont(FONT_MEDIUM, 7.5)
    c.setFillColor(COLOR_TEXT_PRIMARY)

    c.drawString(x, y, label)

    label_width = c.stringWidth(label, FONT_MEDIUM, 7.5)

    # divider
    divider_x = x + label_width + 4

    c.setStrokeColor(COLOR_BORDER_DIVIDER)
    c.setLineWidth(0.5)

    c.line(
        divider_x,
        y - 2,
        divider_x,
        y + 6,
    )

    # 사건 제목
    c.setFont(FONT_REGULAR, 7)
    c.drawString(divider_x + 4, y, case_title)

    # -------------------------
    # Page number
    # -------------------------

    c.setFont(FONT_REGULAR, 7)

    c.drawRightString(
        PAGE_WIDTH - PAGE_PADDING_RIGHT,
        y,
        f"{page_number:02d}",
    )
