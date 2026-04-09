from reportlab.lib.utils import simpleSplit

from app.doc_generator.base import get_font

from .draw.draw_event_item import (
    CONTENT_CONTAINER_WIDTH,
    CONTENT_PADDING,
    DESC_EVIDENCE_GAP,
    DESCRIPTION_FONT_SIZE,
    EVIDENCE_FONT_SIZE,
    LINE_HEIGHT_RATIO,
    TITLE_DESC_GAP,
    TITLE_FONT_SIZE,
)

FONT_MEDIUM = get_font("medium")
FONT_BOLD = get_font("bold")
FONT_REGULAR = get_font("regular")


def calculate_event_item_layout(
    title: str,
    description: str,
    evidence_text: str,
):
    # -------------------------
    # TEXT WRAP
    # -------------------------
    text_width = CONTENT_CONTAINER_WIDTH - (CONTENT_PADDING * 2)

    title_lines = simpleSplit(
        title,
        FONT_BOLD,
        TITLE_FONT_SIZE,
        text_width,
    )

    desc_lines = simpleSplit(
        description,
        FONT_REGULAR,
        DESCRIPTION_FONT_SIZE,
        text_width,
    )

    evidence_lines = simpleSplit(
        evidence_text,
        FONT_MEDIUM,
        EVIDENCE_FONT_SIZE,
        text_width,
    )

    # -------------------------
    # HEIGHT CALCULATION
    # -------------------------

    title_height = len(title_lines) * TITLE_FONT_SIZE * LINE_HEIGHT_RATIO
    desc_height = len(desc_lines) * DESCRIPTION_FONT_SIZE * LINE_HEIGHT_RATIO
    evidence_height = len(evidence_lines) * EVIDENCE_FONT_SIZE * LINE_HEIGHT_RATIO

    content_height = (
        CONTENT_PADDING
        + title_height
        + TITLE_DESC_GAP
        + desc_height
        + DESC_EVIDENCE_GAP
        + evidence_height
        + CONTENT_PADDING
    )

    return {
        "title_lines": title_lines,
        "desc_lines": desc_lines,
        "evidence_lines": evidence_lines,
        "height": content_height,
    }
