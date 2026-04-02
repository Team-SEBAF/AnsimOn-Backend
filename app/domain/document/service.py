from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.base.base_error import CodeException
from app.domain.document.errors import GetDocumentErrorCode
from app.domain.document.models import Document
from app.domain.document.repos import DocumentRepository
from app.domain.document.schemas import (
    ComplaintFormData,
    PatchComplaintFormDataRequest,
    PatchStatementFormDataRequest,
    StatementFormData,
)


class DocumentService:
    @classmethod
    def _deep_merge_dict(cls, base: dict[str, Any], patch: dict[str, Any]) -> None:
        """patch의 값이 빈 dict면 해당 키를 비우고, 아니면 dict끼리는 재귀 병합."""
        for k, v in patch.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                if not v:
                    base[k] = v
                else:
                    cls._deep_merge_dict(base[k], v)
            else:
                base[k] = v

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

    def patch_complaint_form_data(
        self,
        complaint_id: UUID,
        body: PatchComplaintFormDataRequest,
        db: Session,
    ) -> ComplaintFormData:
        doc = self._get_document_or_raise(complaint_id, db)
        current: dict[str, Any] = dict(doc.complaint_form_data or {})

        patch = body.model_dump(exclude_unset=True, mode="json")
        if patch:
            self._deep_merge_dict(current, patch)
        validated = ComplaintFormData.model_validate(current)
        doc.complaint_form_data = validated.model_dump(mode="json")
        flag_modified(doc, "complaint_form_data")

        doc.need_complaint_pdf_regeneration = True

        db.commit()
        db.refresh(doc)

        return ComplaintFormData.model_validate(doc.complaint_form_data or {})

    def patch_statement_form_data(
        self,
        complaint_id: UUID,
        body: PatchStatementFormDataRequest,
        db: Session,
    ) -> StatementFormData:
        doc = self._get_document_or_raise(complaint_id, db)
        current: dict[str, Any] = dict(doc.statement_form_data or {})

        patch = body.model_dump(exclude_unset=True, mode="json")
        for k, v in patch.items():
            current[k] = v
        validated = StatementFormData.model_validate(current)
        doc.statement_form_data = validated.model_dump(mode="json")
        flag_modified(doc, "statement_form_data")

        doc.need_statement_pdf_regeneration = True

        db.commit()
        db.refresh(doc)

        return StatementFormData.model_validate(doc.statement_form_data or {})


document_service = DocumentService()
