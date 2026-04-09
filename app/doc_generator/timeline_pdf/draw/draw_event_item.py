from reportlab.pdfgen.canvas import Canvas

from app.doc_generator.base import get_font
from app.doc_generator.timeline_pdf.color_constants import (
    COLOR_BORDER_DIVIDER,
    COLOR_TEXT_SECONDARY,
)
from app.doc_generator.timeline_pdf.layout_constants import (
    PAGE_PADDING_LEFT,
)

# -------------------------
# FIGMA CONSTANTS
# -------------------------

TIMELINE_VERTICAL_LINE_CONTAINER_WIDTH = 22

TIME_CONTAINER_WIDTH = 48
CONTENT_CONTAINER_WIDTH = 477

CONTENT_PADDING = 14

TITLE_DESC_GAP = 2
DESC_EVIDENCE_GAP = 8

TITLE_FONT_SIZE = 8.5
DESCRIPTION_FONT_SIZE = 8
EVIDENCE_FONT_SIZE = 7
TIME_FONT_SIZE = 7.5

LINE_HEIGHT_RATIO = 1.4

# -------------------------
# FONT
# -------------------------

FONT_MEDIUM = get_font("medium")
FONT_BOLD = get_font("bold")
FONT_REGULAR = get_font("regular")


def draw_event_item(
    c: Canvas,
    start_y: float,
    layout: dict,
    time_text: str,
    on_border: bool = True,
):
    # -------------------------
    # X POSITIONS
    # -------------------------

    timeline_x = PAGE_PADDING_LEFT + TIMELINE_VERTICAL_LINE_CONTAINER_WIDTH

    time_x = timeline_x
    content_x = time_x + TIME_CONTAINER_WIDTH

    title_lines = layout["title_lines"]
    desc_lines = layout["desc_lines"]
    evidence_lines = layout["evidence_lines"]
    content_height = layout["height"]

    # -------------------------
    # BORDER TOP
    # -------------------------

    if on_border:
        c.setStrokeColor(COLOR_BORDER_DIVIDER)
        c.setLineWidth(0.5)

        c.line(
            content_x,
            start_y,
            content_x + CONTENT_CONTAINER_WIDTH,
            start_y,
        )

    # -------------------------
    # TITLE
    # -------------------------

    text_y = start_y - CONTENT_PADDING - TITLE_FONT_SIZE

    c.setFont(FONT_BOLD, TITLE_FONT_SIZE)
    c.setFillColorRGB(0, 0, 0)

    for line in title_lines:
        c.drawString(
            content_x + CONTENT_PADDING,
            text_y,
            line,
        )
        text_y -= TITLE_FONT_SIZE * LINE_HEIGHT_RATIO

    text_y -= TITLE_DESC_GAP

    # -------------------------
    # DESCRIPTION
    # -------------------------

    c.setFont(FONT_REGULAR, DESCRIPTION_FONT_SIZE)

    for line in desc_lines:
        c.drawString(
            content_x + CONTENT_PADDING,
            text_y,
            line,
        )
        text_y -= DESCRIPTION_FONT_SIZE * LINE_HEIGHT_RATIO

    text_y -= DESC_EVIDENCE_GAP

    # -------------------------
    # EVIDENCE NUMBER
    # -------------------------

    c.setFont(FONT_MEDIUM, EVIDENCE_FONT_SIZE)
    c.setFillColor(COLOR_TEXT_SECONDARY)

    for line in evidence_lines:
        c.drawString(
            content_x + CONTENT_PADDING,
            text_y,
            line,
        )
        text_y -= EVIDENCE_FONT_SIZE * LINE_HEIGHT_RATIO

    # -------------------------
    # HEIGHT RESULT
    # -------------------------

    end_y = start_y - content_height
    center_y = start_y - (content_height / 2)

    # -------------------------
    # TIME TEXT (CENTER ALIGN)
    # -------------------------

    time_y = center_y - (TIME_FONT_SIZE / 2)

    c.setFont(FONT_MEDIUM, TIME_FONT_SIZE)
    c.setFillColorRGB(0, 0, 0)

    c.drawString(
        time_x + CONTENT_PADDING,
        time_y,
        time_text,
    )

    return center_y, end_y
