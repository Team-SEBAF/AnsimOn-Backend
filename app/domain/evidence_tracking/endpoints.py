from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_TRACKING_RESTRICT
from app.domain.evidence_tracking import schemas
from app.domain.evidence_tracking.service import evidence_tracking_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Tracking"])


@router.post(
    "/{complaint_id}/evidences/trackings",
    summary=f"TRACKING 타입 증거 영상 업로드 (최대 {EVIDENCE_TRACKING_RESTRICT.max_count}개)",
    description="TRACKING 타입 증거 영상을 업로드합니다.",
    response_model=schemas.EvidenceTrackingUploadResponse,
    responses=evidence_errors.EVIDENCE_MAX_COUNT_EXCEEDED_ERRORS_RESPONSES,
)
def upload_evidence_tracking_videos(
    complaint: Complaint = Depends(get_owned_complaint),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    return evidence_tracking_service.upload_trackings(
        complaint=complaint,
        files=files,
        db=db,
    )


@router.get(
    "/{complaint_id}/evidences/trackings/previews",
    summary="TRACKING 타입 증거 프리뷰 리스트 조회 (썸네일 이미지 1시간 유효)",
    description="TRACKING 타입 증거 프리뷰 리스트를 조회합니다.",
    response_model=schemas.EvidenceTrackingPreviewListResponse,
)
def get_evidence_tracking_previews(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return evidence_tracking_service.get_preview_trackings(
        complaint=complaint,
        limit=limit,
        db=db,
    )


@router.get(
    "/evidence/tracking/{tracking_id}/original",
    summary="TRACKING 타입 증거 영상 원본 조회 (10분 유효)",
    description="TRACKING 타입 증거 영상 원본을 조회합니다.",
    response_model=schemas.EvidenceTrackingOriginalResponse,
    responses=evidence_errors.GET_EVIDENCE_ERRORS_RESPONSES,
)
def get_evidence_tracking_original(
    tracking_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_tracking_service.get_original_tracking(
        tracking_id=tracking_id,
        current_user=current_user,
        db=db,
    )
