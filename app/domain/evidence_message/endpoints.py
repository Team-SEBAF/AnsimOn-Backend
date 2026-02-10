from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_MESSAGE_RESTRICT
from app.domain.evidence_message import schemas
from app.domain.evidence_message.service import evidence_message_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Message"])


@router.post(
    "/{complaint_id}/evidences/messages",
    summary=f"MESSAGE 타입 증거 이미지 업로드 (최대 {EVIDENCE_MESSAGE_RESTRICT.max_count}개)",
    description="MESSAGE 타입 증거 이미지를 업로드합니다.",
    response_model=schemas.EvidenceMessageUploadResponse,
    responses=evidence_errors.EVIDENCE_MAX_COUNT_EXCEEDED_ERRORS_RESPONSES,
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
    "/{complaint_id}/evidences/messages/thumbnails",
    summary="MESSAGE 타입 증거 썸네일 리스트 조회",
    description="MESSAGE 타입 증거 썸네일 리스트를 조회합니다. (1시간 유효)",
    response_model=schemas.EvidenceMessageThumbnailListResponse,
)
def get_evidence_message_thumbnails(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return evidence_message_service.get_thumbnail_images(
        complaint=complaint,
        limit=limit,
        db=db,
    )


@router.get(
    "/{complaint_id}/evidences/messages/details",
    summary="MESSAGE 타입 증거 상세 리스트 조회",
    description="MESSAGE 타입 증거 상세 리스트를 조회합니다. (30분 유효)",
    response_model=schemas.EvidenceMessageDetailListResponse,
)
def get_evidence_message_details(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return evidence_message_service.get_detail_images(
        complaint=complaint,
        limit=limit,
        db=db,
    )


@router.get(
    "/{message_id}/original-image",
    summary="MESSAGE 타입 증거 이미지 원본 조회",
    description="MESSAGE 타입 증거 이미지 원본을 조회합니다. (10분 유효)",
    response_model=schemas.EvidenceMessageOriginalImageResponse,
    responses=evidence_errors.GET_EVIDENCE_ERRORS_RESPONSES,
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
