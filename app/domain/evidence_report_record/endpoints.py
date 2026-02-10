from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence_report_record import schemas
from app.domain.evidence_report_record.service import evidence_report_record_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Report Record"])


@router.post(
    "/{complaint_id}/evidences/report-records",
    summary=f"REPORT_RECORD 타입 신고・사건 일지 업로드 (최대 {EVIDENCE_DOCUMENT_RESTRICT.max_count}개)",
    description="REPORT_RECORD 타입 신고・사건 일지를 업로드합니다.",
    response_model=schemas.EvidenceReportRecordUploadResponse,
    responses=evidence_errors.EVIDENCE_MAX_COUNT_EXCEEDED_ERRORS_RESPONSES,
)
def upload_evidence_report_records(
    complaint: Complaint = Depends(get_owned_complaint),
    files: list[UploadFile] = File(...),  # multipart/form-data
    db: Session = Depends(get_db),
):
    return evidence_report_record_service.upload_report_records(
        complaint=complaint,
        files=files,
        db=db,
    )
