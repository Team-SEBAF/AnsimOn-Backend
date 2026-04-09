from io import BytesIO
from pathlib import Path

from docxtpl import DocxTemplate

from app.doc_generator.complaint_docx.context import build_complaint_context
from app.domain.document.schemas.form_data import ComplaintFormData

_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "complaint_template.docx"


def build_complaint_docx_bytes(
    complaint_form_data: ComplaintFormData,
) -> bytes:
    ctx = build_complaint_context(complaint_form_data)
    doc = DocxTemplate(_TEMPLATE_PATH)
    doc.render(ctx)
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()
