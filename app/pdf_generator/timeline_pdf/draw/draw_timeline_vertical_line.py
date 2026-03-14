from reportlab.pdfgen.canvas import Canvas

from app.pdf_generator.timeline_pdf.draw.draw_group_header import (
    TIMELINE_VERTICAL_LINE_CONTAINER_WIDTH,
)
from app.pdf_generator.timeline_pdf.layout_constants import (
    CONTENT_BOTTOM_Y,
    PAGE_PADDING_LEFT,
)

LINE_WIDTH = 1

GROUP_RADIUS = 3
EVENT_RADIUS = 2.3

# 마지막 원 이후 추가 길이
LINE_EXTENSION = 50


def draw_timeline_vertical_line(
    c: Canvas,
    timeline_points: list,
    is_last_page: bool,
):
    if not timeline_points:
        return

    x = PAGE_PADDING_LEFT + (TIMELINE_VERTICAL_LINE_CONTAINER_WIDTH / 2)

    ys = [p["y"] for p in timeline_points]

    top_y = max(ys)
    bottom_y = min(ys)

    # -------------------------
    # line extension
    # -------------------------

    if not is_last_page:
        bottom_y -= LINE_EXTENSION

    # content 영역 넘지 않도록 제한
    if bottom_y < CONTENT_BOTTOM_Y:
        bottom_y = CONTENT_BOTTOM_Y

    # -------------------------
    # DRAW LINE
    # -------------------------

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(LINE_WIDTH)

    c.line(
        x,
        bottom_y,
        x,
        top_y,
    )

    # -------------------------
    # DRAW CIRCLES
    # -------------------------

    for point in timeline_points:
        y = point["y"]

        if point["type"] == "group":
            c.setFillColorRGB(0, 0, 0)

            c.circle(
                x,
                y,
                GROUP_RADIUS,
                fill=1,
                stroke=0,
            )

        else:
            c.setFillColorRGB(1, 1, 1)
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(1)

            c.circle(
                x,
                y,
                EVENT_RADIUS,
                fill=1,
                stroke=1,
            )
