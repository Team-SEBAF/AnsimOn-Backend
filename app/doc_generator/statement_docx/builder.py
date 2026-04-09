from io import BytesIO
from pathlib import Path

from docxtpl import DocxTemplate

from app.doc_generator.statement_docx.context import build_statement_context
from app.domain.document.schemas.form_data import StatementFormData

_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "statement_template.docx"


def build_statement_docx_bytes(statement_form_data: StatementFormData) -> bytes:
    ctx = build_statement_context(statement_form_data)
    doc = DocxTemplate(_TEMPLATE_PATH)
    doc.render(ctx)
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()
