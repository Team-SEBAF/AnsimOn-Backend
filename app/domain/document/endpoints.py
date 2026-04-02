from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.document.errors import GET_DOCUMENT_ERRORS_RESPONSES
from app.domain.document.schemas import (
    ComplaintFormData,
    PatchComplaintFormDataRequest,
    PatchStatementFormDataRequest,
    StatementFormData,
)
from app.domain.document.service import document_service

router = APIRouter(prefix="/api/v1", tags=["Document"])


@router.get(
    "/{complaint_id}/document/complaint-form-data",
    summary="고소장 폼 데이터 조회",
    description="Step 03 고소장 폼 데이터를 조회합니다.",
    response_model=ComplaintFormData,
    responses=GET_DOCUMENT_ERRORS_RESPONSES,
)
def get_complaint_form_data(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return document_service.get_complaint_form_data(complaint.complaint_id, db)


@router.patch(
    "/{complaint_id}/document/complaint-form-data",
    summary="고소장 폼 데이터 수정",
    description="Step 03 고소장 폼 데이터를 부분 수정합니다. 수정할 필드만 요청 본문에 보내주세요.",
    response_model=ComplaintFormData,
    responses=GET_DOCUMENT_ERRORS_RESPONSES,
)
def patch_complaint_form_data(
    complaint: Complaint = Depends(get_owned_complaint),
    body: PatchComplaintFormDataRequest = Body(...),
    db: Session = Depends(get_db),
):
    return document_service.patch_complaint_form_data(complaint.complaint_id, body, db)


@router.get(
    "/{complaint_id}/document/statement-form-data",
    summary="진술서 폼 데이터 조회",
    description="Step 03 진술서 폼 데이터를 조회합니다.",
    response_model=StatementFormData,
    responses=GET_DOCUMENT_ERRORS_RESPONSES,
)
def get_statement_form_data(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return document_service.get_statement_form_data(complaint.complaint_id, db)


@router.patch(
    "/{complaint_id}/document/statement-form-data",
    summary="진술서 폼 데이터 수정",
    description="Step 03 진술서 폼 데이터를 부분 수정합니다. 수정할 필드만 요청 본문에 보내주세요.",
    response_model=StatementFormData,
    responses=GET_DOCUMENT_ERRORS_RESPONSES,
)
def patch_statement_form_data(
    complaint: Complaint = Depends(get_owned_complaint),
    body: PatchStatementFormDataRequest = Body(...),
    db: Session = Depends(get_db),
):
    return document_service.patch_statement_form_data(complaint.complaint_id, body, db)
