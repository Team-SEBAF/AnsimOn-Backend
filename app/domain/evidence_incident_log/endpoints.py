from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence_incident_log import schemas
from app.domain.evidence_incident_log.errors import INCIDENT_LOG_ACCESS_AND_TYPE_CHECK_RESPONSES
from app.domain.evidence_incident_log.service import evidence_incident_log_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Incident Log"])


@router.post(
    "/{complaint_id}/evidences/incident-logs/file",
    summary=f"INCIDENT_LOG 타입 사건 일지 파일 업로드 (파일 + 폼데이터, 최대 {EVIDENCE_DOCUMENT_RESTRICT.max_count}개)",
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


@router.get(
    "/{complaint_id}/evidences/incident-logs/previews",
    summary="INCIDENT_LOG 타입 사건 일지 프리뷰 리스트 조회",
    description="INCIDENT_LOG 타입 사건 일지 프리뷰 리스트를 조회합니다.",
    response_model=schemas.EvidenceIncidentLogPreviewListResponse,
)
def get_evidence_incident_log_previews(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.get_preview_incident_logs(
        complaint=complaint,
        limit=limit,
        db=db,
    )


@router.get(
    "/{complaint_id}/evidences/incident-logs/details",
    summary="INCIDENT_LOG 타입 사건 일지 상세 리스트 조회",
    description="INCIDENT_LOG 타입 사건 일지 상세 리스트를 조회합니다.",
    response_model=schemas.EvidenceIncidentLogDetailListResponse,
)
def get_evidence_incident_log_details(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.get_detail_incident_logs(
        complaint=complaint,
        limit=limit,
        db=db,
    )


@router.get(
    "/evidence/incident-log-file/{incident_log_id}/original",
    summary="INCIDENT_LOG 타입 사건 일지 원본 조회 (10분 유효)",
    description="INCIDENT_LOG 타입 사건 일지 원본을 조회합니다.",
    response_model=schemas.EvidenceIncidentLogFileOriginalResponse,
    responses=INCIDENT_LOG_ACCESS_AND_TYPE_CHECK_RESPONSES,
)
def get_evidence_incident_log_original(
    incident_log_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.get_original_incident_log_file(
        incident_log_id=incident_log_id,
        current_user=current_user,
        db=db,
    )


@router.post(
    "/{complaint_id}/evidences/incident-logs/form-data",
    summary=f"INCIDENT_LOG 타입 사건 일지 폼 데이터 업로드 (파일 + 폼데이터, 최대 {EVIDENCE_DOCUMENT_RESTRICT.max_count}개)",
    description="INCIDENT_LOG 타입 사건 일지 폼 데이터를 업로드합니다.",
    response_model=schemas.EvidenceIncidentLogFormDataResponse,
)
def upload_evidence_incident_log_form_data(
    request: schemas.EvidenceIncidentLogFormDataUploadRequest,
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.upload_incident_log_form_data(
        complaint=complaint,
        request=request,
        db=db,
    )


@router.get(
    "/evidence/incident-log-form-data/{incident_log_id}",
    summary="INCIDENT_LOG 타입 사건 일지 폼 데이터 조회",
    description="INCIDENT_LOG 타입 사건 일지 폼 데이터를 조회합니다.",
    response_model=schemas.EvidenceIncidentLogFormDataResponse,
    responses=INCIDENT_LOG_ACCESS_AND_TYPE_CHECK_RESPONSES,
)
def get_incident_log_form_data(
    incident_log_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.get_incident_log_form_data(
        incident_log_id=incident_log_id,
        current_user=current_user,
        db=db,
    )


@router.patch(
    "/evidences/incident-logs/form-data/{incident_log_id}",
    summary="INCIDENT_LOG 타입 사건 일지 폼 데이터 수정",
    description="INCIDENT_LOG 타입 사건 일지 폼 데이터를 수정합니다.",
    response_model=schemas.EvidenceIncidentLogFormDataResponse,
    responses=INCIDENT_LOG_ACCESS_AND_TYPE_CHECK_RESPONSES,
)
def update_evidence_incident_log_form_data(
    incident_log_id: UUID,
    request: schemas.EvidenceIncidentLogFormDataUpdateRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.update_incident_log_form_data(
        incident_log_id=incident_log_id,
        request=request,
        current_user=current_user,
        db=db,
    )
