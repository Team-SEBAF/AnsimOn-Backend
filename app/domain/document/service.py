from uuid import UUID

from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.domain.document.errors import GetDocumentErrorCode
from app.domain.document.models import Document
from app.domain.document.repos import DocumentRepository
from app.domain.document.schemas import ComplaintFormData, StatementFormData


class DocumentService:
    def _get_document_or_raise(self, complaint_id: UUID, db: Session) -> Document:
        doc = DocumentRepository(db).get_by_complaint_id(complaint_id)
        if doc is None:
            raise CodeException(
                code=GetDocumentErrorCode.DOCUMENT_NOT_FOUND,
                message="문서를 찾을 수 없습니다.",
                debug_message=f"complaint_id: {complaint_id}에 해당하는 documents 행이 없습니다.",
                status_code=404,
            )
        return doc

    def get_complaint_form_data(self, complaint_id: UUID, db: Session) -> ComplaintFormData:
        doc = self._get_document_or_raise(complaint_id, db)
        raw = doc.complaint_form_data if doc.complaint_form_data is not None else {}
        return ComplaintFormData.model_validate(raw)

    def get_statement_form_data(self, complaint_id: UUID, db: Session) -> StatementFormData:
        doc = self._get_document_or_raise(complaint_id, db)
        raw = doc.statement_form_data if doc.statement_form_data is not None else {}
        return StatementFormData.model_validate(raw)


document_service = DocumentService()
