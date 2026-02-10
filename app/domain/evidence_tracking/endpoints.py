from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
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
