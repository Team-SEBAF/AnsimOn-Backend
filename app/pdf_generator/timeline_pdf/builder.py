from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .footer import draw_footer
from .header import draw_header


def build_timeline_pdf_bytes(case_title: str, author: str) -> bytes:
    """타임라인 PDF를 bytes로 생성. 이후 S3 등 스토리지에 저장용."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    today = datetime.today().strftime("%Y년 %m월 %d일")

    draw_header(c, case_title, today, author)
    draw_footer(c, 1, case_title)

    c.showPage()
    c.save()
    return buffer.getvalue()
