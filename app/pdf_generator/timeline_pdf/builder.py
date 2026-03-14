from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.pdf_generator.timeline_pdf.draw.draw_event_item import draw_event_item
from app.pdf_generator.timeline_pdf.draw.draw_group_header import draw_group_header
from app.pdf_generator.timeline_pdf.layout_constants import CONTENT_TOP_Y
from app.pdf_generator.timeline_pdf.utils import (
    extract_date_group_header_data,
    extract_event_item_data,
)

from .footer import draw_footer
from .header import draw_header


def build_timeline_pdf_bytes(
    case_title: str,
    author: str,
    timeline_json: dict,
) -> bytes:
    """타임라인 PDF를 bytes로 생성. 이후 S3 등 스토리지에 저장용."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    today = datetime.today().strftime("%Y년 %m월 %d일")

    draw_header(c, case_title, today, author)
    draw_footer(c, 1, case_title)

    # 첫 번째 date group만 (디자인 확인용)
    items = timeline_json.get("items", [])
    if items:
        first = items[0]
        header_data = extract_date_group_header_data(first)
        _, end_y = draw_group_header(
            c,
            start_y=CONTENT_TOP_Y,
            date_text=header_data["date_text"],
            total_count=header_data["total_count"],
            evidence_number=header_data["evidence_number"],
        )

        first_event = first["events"][0]
        event_data = extract_event_item_data(
            time=first_event["time"],
            evidence=first_event["evidences"][0],
        )
        draw_event_item(
            c,
            start_y=end_y,
            time_text=event_data["time_text"],
            title=event_data["title"],
            description=event_data["description"],
            evidence_text=event_data["evidence_text"],
            on_border=False,
        )

    c.showPage()
    c.save()
    return buffer.getvalue()
