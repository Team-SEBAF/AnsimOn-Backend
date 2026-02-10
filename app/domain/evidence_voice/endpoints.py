from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_VOICE_RESTRICT
from app.domain.evidence_voice import schemas
from app.domain.evidence_voice.service import evidence_voice_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Voice"])


@router.post(
    "/{complaint_id}/evidences/voices",
    summary=f"VOICE 타입 증거 음성 업로드 (최대 {EVIDENCE_VOICE_RESTRICT.max_count}개)",
    description="VOICE 타입 증거 음성을 업로드합니다.",
    response_model=schemas.EvidenceVoiceUploadResponse,
    responses=evidence_errors.EVIDENCE_MAX_COUNT_EXCEEDED_ERRORS_RESPONSES,
)
def upload_evidence_voices(
    complaint: Complaint = Depends(get_owned_complaint),
    files: list[UploadFile] = File(...),  # multipart/form-data
    db: Session = Depends(get_db),
):
    return evidence_voice_service.upload_voices(
        complaint=complaint,
        files=files,
        db=db,
    )
