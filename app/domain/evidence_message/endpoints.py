from uuid import UUID

from fastapi import APIRouter, Depends, Query
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
    "/{complaint_id}/evidences/messages/register",
    summary=f"MESSAGE 타입 증거 Presigned URL로 S3 업로드 완료 후, 메타데이터 DB 저장 + 썸네일/상세 이미지 생성 (복수 업로드 지원, 최대 {EVIDENCE_MESSAGE_RESTRICT.max_count}개)",
    description="Presigned URL로 S3 업로드 완료 후 호출하세요. 썸네일/상세 이미지는 백엔드에서 생성합니다.",
    response_model=schemas.EvidenceMessageRegisterListResponse,
    responses=evidence_errors.REGISTER_EVIDENCE_ERRORS_RESPONSES,
)
def register_message(
    complaint: Complaint = Depends(get_owned_complaint),
    request: schemas.EvidenceMessageRegisterRequest = ...,
    db: Session = Depends(get_db),
):
    return evidence_message_service.register_message(
        complaint=complaint,
        request=request,
        db=db,
    )


@router.get(
    "/{complaint_id}/evidences/messages/previews",
    summary="MESSAGE 타입 증거 프리뷰 리스트 조회 (썸네일 이미지 1시간 유효)",
    description="MESSAGE 타입 증거 프리뷰 리스트를 조회합니다.",
    response_model=schemas.EvidenceMessagePreviewListResponse,
)
def get_evidence_message_previews(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return evidence_message_service.get_preview_messages(
        complaint=complaint,
        limit=limit,
        db=db,
    )


@router.get(
    "/{complaint_id}/evidences/messages/details",
    summary="MESSAGE 타입 증거 상세 리스트 조회 (썸네일 이미지 30분 유효)",
    description="MESSAGE 타입 증거 상세 리스트를 조회합니다.",
    response_model=schemas.EvidenceMessageDetailListResponse,
)
def get_evidence_message_details(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return evidence_message_service.get_detail_messages(
        complaint=complaint,
        limit=limit,
        db=db,
    )


@router.get(
    "/evidence/message/{message_id}/original",
    summary="MESSAGE 타입 증거 이미지 원본 조회 (원본 이미지 10분 유효)",
    description="MESSAGE 타입 증거 이미지 원본을 조회합니다.",
    response_model=schemas.EvidenceMessageOriginalImageResponse,
    responses=evidence_errors.GET_EVIDENCE_ERRORS_RESPONSES,
)
def get_evidence_message_original(
    message_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_message_service.get_original_message(
        message_id=message_id,
        current_user=current_user,
        db=db,
    )
