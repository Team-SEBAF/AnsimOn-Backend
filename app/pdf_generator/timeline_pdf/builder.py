from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.pdf_generator.timeline_pdf.layout_pages import layout_pages
from app.pdf_generator.timeline_pdf.render_pages import render_pages

from .footer import draw_footer
from .header import draw_header


def build_timeline_pdf_bytes(
    case_title: str,
    author: str,
    timeline_json: dict,
) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    today = datetime.today().strftime("%Y년 %m월 %d일")

    pages = layout_pages(timeline_json)

    timeline_points_all = []

    page_number = 1

    for page in pages:
        draw_header(c, case_title, today, author)
        draw_footer(c, page_number, case_title)

        points = render_pages(c, [page])

        timeline_points_all.extend(points)

        c.showPage()

        page_number += 1

    c.save()

    return buffer.getvalue()
