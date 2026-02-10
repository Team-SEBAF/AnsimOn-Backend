from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence_incident_log import schemas
from app.domain.evidence_incident_log.service import evidence_incident_log_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Incident Log"])


@router.post(
    "/{complaint_id}/evidences/incident-logs/file",
    summary=f"INCIDENT_LOG 타입 사건 일지 파일 업로드 (최대 {EVIDENCE_DOCUMENT_RESTRICT.max_count}개)",
    description="INCIDENT_LOG 타입 사건 일지 파일을 업로드합니다.",
    response_model=schemas.EvidenceIncidentLogFileUploadResponse,
    responses=evidence_errors.EVIDENCE_MAX_COUNT_EXCEEDED_ERRORS_RESPONSES,
)
def upload_evidence_report_records(
    complaint: Complaint = Depends(get_owned_complaint),
    files: list[UploadFile] = File(...),  # multipart/form-data
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.upload_incident_log_files(
        complaint=complaint,
        files=files,
        db=db,
    )
