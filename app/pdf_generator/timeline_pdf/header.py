from pathlib import Path

from reportlab.pdfgen.canvas import Canvas

from app.pdf_generator.base import get_font
from app.pdf_generator.color_constants import (
    COLOR_BORDER_DIVIDER,
    COLOR_BORDER_LIGHT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from app.pdf_generator.timeline_pdf.layout_constants import (
    HEADER_BOTTOM_Y,
    HEADER_RIGHT_WIDTH,
    HEADER_TOP_Y,
    PAGE_PADDING_LEFT,
    PAGE_PADDING_RIGHT,
    PAGE_WIDTH,
)

# -------------------------
# Font cache
# -------------------------

FONT_REGULAR = get_font("regular")
FONT_MEDIUM = get_font("medium")
FONT_SEMIBOLD = get_font("semibold")

LOGO_PATH = Path(__file__).parent.parent / "static" / "AnsimOn_Icon.png"


def draw_header(
    c: Canvas,
    case_title: str,
    created_date: str,
    author: str,
):
    x = PAGE_PADDING_LEFT
    y = HEADER_TOP_Y

    # -------------------------
    # LEFT CONTAINER
    # -------------------------

    # 사건 타임라인
    c.setFont(FONT_MEDIUM, 8)
    c.setFillColor(COLOR_TEXT_SECONDARY)
    c.drawString(x, y - 10, "사건 타임라인")

    # 사건 제목
    c.setFont(FONT_SEMIBOLD, 14)
    c.setFillColor(COLOR_TEXT_PRIMARY)
    c.drawString(x, y - 26, case_title)

    # 작성일 / 작성자 영역
    meta_y = y - 42

    # 작성일 label
    label = "작성일"

    c.setFont(FONT_MEDIUM, 7.5)
    c.setFillColor(COLOR_TEXT_PRIMARY)
    c.drawString(x, meta_y, label)

    label_width = c.stringWidth(label, FONT_MEDIUM, 7.5)

    # divider line
    divider_x = x + label_width + 4

    c.setStrokeColor(COLOR_BORDER_DIVIDER)
    c.setLineWidth(0.5)

    c.line(
        divider_x,
        meta_y - 2,
        divider_x,
        meta_y + 6,
    )

    # 날짜 값
    date_x = divider_x + 4

    c.setFont(FONT_REGULAR, 7)
    c.drawString(date_x, meta_y, created_date)

    date_width = c.stringWidth(created_date, FONT_REGULAR, 7)

    # 작성자
    author_x = date_x + date_width + 24

    author_label = "작성자"

    c.setFont(FONT_MEDIUM, 7.5)
    c.drawString(author_x, meta_y, author_label)

    author_width = c.stringWidth(author_label, FONT_MEDIUM, 7.5)

    divider_x2 = author_x + author_width + 4

    c.line(
        divider_x2,
        meta_y - 2,
        divider_x2,
        meta_y + 6,
    )

    c.setFont(FONT_REGULAR, 7)
    c.drawString(divider_x2 + 4, meta_y, author)

    # -------------------------
    # RIGHT CONTAINER
    # -------------------------

    right_x = PAGE_WIDTH - PAGE_PADDING_RIGHT - HEADER_RIGHT_WIDTH

    # header vertical center
    header_center_y = (HEADER_TOP_Y + HEADER_BOTTOM_Y) / 2

    # icon
    icon_height = 10
    icon_x = right_x
    icon_y = header_center_y - icon_height / 2

    if LOGO_PATH.exists():
        c.drawImage(
            str(LOGO_PATH),
            icon_x,
            icon_y,
            width=10.9,
            height=icon_height,
            preserveAspectRatio=True,
            mask="auto",
        )

    # vertical divider
    divider_x = icon_x + 18

    c.setStrokeColor(COLOR_BORDER_LIGHT)
    c.setLineWidth(0.5)

    c.line(
        divider_x,
        HEADER_BOTTOM_Y,
        divider_x,
        HEADER_TOP_Y,
    )

    # 안내문 텍스트
    text_x = divider_x + 8

    c.setFont(FONT_REGULAR, 6)
    c.setFillColor(COLOR_TEXT_SECONDARY)

    notice = [
        "본 문서의 경우 법적 증거 자료 제출 시 효력이",
        "발생될 수 있는 자료이며, 작성함에 있어 거짓되",
        "지 않음에 동의한 문서임을 밝힙니다.",
    ]

    line_height = 8
    text_block_height = len(notice) * line_height

    text_y = header_center_y + text_block_height / 2 - line_height

    for i, line in enumerate(notice):
        c.drawString(text_x, text_y - (i * line_height), line)
