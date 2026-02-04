from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

import app.domain.evidence.message.errors as evidence_message_errors
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.message import schemas
from app.domain.evidence.message.service import evidence_message_service

router = APIRouter(prefix="/api/v1/evidence-messages", tags=["Evidence Message"])


@router.post(
    "/{complaint_id}/messages",
    summary="MESSAGE 타입 증거 이미지 업로드",
    description="MESSAGE 타입 증거 이미지를 업로드합니다.",
    response_model=schemas.EvidenceMessageUploadResponse,
)
def upload_evidence_message_images(
    complaint: Complaint = Depends(get_owned_complaint),
    files: list[UploadFile] = File(...),  # multipart/form-data
    db: Session = Depends(get_db),
):
    return evidence_message_service.upload_images(
        complaint=complaint,
        files=files,
        db=db,
    )


@router.get(
    "/{message_id}/original-image",
    summary="MESSAGE 타입 증거 이미지 원본 조회",
    description="MESSAGE 타입 증거 이미지 원본을 조회합니다.",
    response_model=schemas.EvidenceMessageOriginalImageResponse,
    responses=evidence_message_errors.GET_EVIDENCE_MESSAGE_ERRORS_RESPONSES,
)
def get_evidence_message_original(
    message_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_message_service.get_original_image(
        message_id=message_id,
        current_user=current_user,
        db=db,
    )
