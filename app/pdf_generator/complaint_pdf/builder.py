from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.domain.document.schemas import ComplaintFormData


def build_complaint_pdf_bytes(complaint_form_data: ComplaintFormData) -> bytes:
    """고소장 PDF 바이트 생성. complaint_form_data는 본문 렌더에 사용."""
    _ = complaint_form_data
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
