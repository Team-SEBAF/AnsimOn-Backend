from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence_report_record import schemas
from app.domain.evidence_report_record.service import evidence_report_record_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Report Record"])


@router.post(
    "/{complaint_id}/evidences/report-records/register",
    summary=f"REPORT_RECORD 타입 신고・사건 일지 Presigned URL로 S3 업로드 완료 후, 메타데이터 DB 저장 (복수 업로드 지원, 최대 {EVIDENCE_DOCUMENT_RESTRICT.max_count}개)",
    description="Presigned URL로 S3 업로드 완료 후 호출하세요.",
    response_model=schemas.EvidenceReportRecordRegisterListResponse,
    responses=evidence_errors.REGISTER_EVIDENCE_ERRORS_RESPONSES,
)
def register_report_record(
    complaint: Complaint = Depends(get_owned_complaint),
    request: schemas.EvidenceReportRecordRegisterRequest = ...,
    db: Session = Depends(get_db),
):
    return evidence_report_record_service.register_report_record(
        complaint=complaint,
        request=request,
        db=db,
    )


@router.get(
    "/{complaint_id}/evidences/report-records/previews",
    summary="REPORT_RECORD 타입 신고・사건 일지 프리뷰 리스트 조회",
    description="REPORT_RECORD 타입 신고・사건 일지 프리뷰 리스트를 조회합니다.",
    response_model=schemas.EvidenceReportRecordPreviewListResponse,
)
def get_evidence_report_record_previews(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return evidence_report_record_service.get_preview_report_records(
        complaint=complaint,
        limit=limit,
        db=db,
    )


@router.get(
    "/{complaint_id}/evidences/report-records/details",
    summary="REPORT_RECORD 타입 신고・사건 일지 상세 리스트 조회",
    description="REPORT_RECORD 타입 신고・사건 일지 상세 리스트를 조회합니다.",
    response_model=schemas.EvidenceReportRecordDetailListResponse,
)
def get_evidence_report_record_details(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return evidence_report_record_service.get_detail_report_records(
        complaint=complaint,
        limit=limit,
        db=db,
    )


@router.get(
    "/evidence/report-record/{report_record_id}/original",
    summary="REPORT_RECORD 타입 신고・사건 일지 원본 조회 (10분 유효)",
    description="REPORT_RECORD 타입 신고・사건 일지 원본을 조회합니다.",
    response_model=schemas.EvidenceReportRecordOriginalResponse,
    responses=evidence_errors.GET_EVIDENCE_ERRORS_RESPONSES,
)
def get_evidence_report_record_original(
    report_record_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_report_record_service.get_original_report_record(
        report_record_id=report_record_id,
        current_user=current_user,
        db=db,
    )
