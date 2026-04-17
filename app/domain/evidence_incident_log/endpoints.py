from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_INCIDENT_LOG_RESTRICT
from app.domain.evidence_incident_log import schemas
from app.domain.evidence_incident_log.errors import INCIDENT_LOG_ACCESS_AND_TYPE_CHECK_RESPONSES
from app.domain.evidence_incident_log.service import evidence_incident_log_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Incident Log"])


@router.post(
    "/{complaint_id}/evidences/incident-logs/file/register",
    summary=f"INCIDENT_LOG 타입 사건 일지 '파일' Presigned URL로 S3 업로드 완료 후, 메타데이터 DB 저장 (복수 업로드 지원, 최대 {EVIDENCE_INCIDENT_LOG_RESTRICT.max_count}개)",
    description="Presigned URL로 S3 업로드 완료 후 호출하세요.",
    response_model=schemas.EvidenceIncidentLogFileRegisterListResponse,
    responses=evidence_errors.REGISTER_EVIDENCE_ERRORS_RESPONSES,
)
def register_incident_log_file(
    complaint: Complaint = Depends(get_owned_complaint),
    request: schemas.EvidenceIncidentLogFileRegisterRequest = ...,
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.register_incident_log_file(
        complaint=complaint,
        request=request,
        db=db,
    )


# @router.get(
#     "/{complaint_id}/evidences/incident-logs/previews",
#     summary="INCIDENT_LOG 타입 사건 일지 '파일' 프리뷰 리스트 조회 [미사용]",
#     description="INCIDENT_LOG 타입 사건 일지 파일 프리뷰 리스트를 조회합니다.",
#     response_model=schemas.EvidenceIncidentLogPreviewListResponse,
# )
# def get_evidence_incident_log_previews(
#     complaint: Complaint = Depends(get_owned_complaint),
#     limit: int = Query(5, ge=1, le=20),
#     db: Session = Depends(get_db),
# ):
#     return evidence_incident_log_service.get_preview_incident_logs(
#         complaint=complaint,
#         limit=limit,
#         db=db,
#     )


@router.get(
    "/{complaint_id}/evidences/incident-logs/details",
    summary="INCIDENT_LOG 타입 사건 일지 '파일' 상세 리스트 조회",
    description="INCIDENT_LOG 타입 사건 일지 파일 상세 리스트를 조회합니다.",
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


# @router.get(
#     "/evidence/incident-log/file/{incident_log_id}/original",
#     summary="INCIDENT_LOG 타입 사건 일지 '파일' 원본 조회 (10분 유효) [미사용]",
#     description="INCIDENT_LOG 타입 사건 일지 파일 원본을 조회합니다.",
#     response_model=schemas.EvidenceIncidentLogFileOriginalResponse,
#     responses=INCIDENT_LOG_ACCESS_AND_TYPE_CHECK_RESPONSES,
# )
# def get_evidence_incident_log_original(
#     incident_log_id: UUID,
#     current_user: AuthUser = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     return evidence_incident_log_service.get_original_incident_log_file(
#         incident_log_id=incident_log_id,
#         current_user=current_user,
#         db=db,
#     )


@router.post(
    "/{complaint_id}/evidences/incident-logs/form-data",
    summary=f"INCIDENT_LOG 타입 사건 일지 '폼 데이터' 업로드 (파일 + 폼데이터, 최대 {EVIDENCE_INCIDENT_LOG_RESTRICT.max_count}개)",
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
    "/evidence/incident-log/form-data/{incident_log_id}",
    summary="INCIDENT_LOG 타입 사건 일지 '폼 데이터' 조회",
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
    "/evidence/incident-log/form-data/{incident_log_id}",
    summary="INCIDENT_LOG 타입 사건 일지 '폼 데이터' 수정 (첨부 자료 해당 X)",
    description="INCIDENT_LOG 타입 사건 일지 폼 데이터를 수정합니다. 첨부 자료 수정은 별도 API로 제공합니다.",
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


@router.post(
    "/{complaint_id}/evidence/incident-log/form-data/{incident_log_id}/attachments/presigned-url",
    summary="INCIDENT_LOG 타입 사건 일지 '폼 데이터' 첨부 자료 Presigned URL 발급 (복수 업로드 지원)",
    description="API Gateway 용량 제한이 10MB이기 때문에, 프론트엔드에서 Presigned URL로 S3에 직접 업로드 후 register API를 호출합니다. 타입 제한 없음.",
    response_model=schemas.FormDataAttachmentPresignedResponse,
)
def get_form_data_attachment_presigned_url(
    complaint: Complaint = Depends(get_owned_complaint),
    incident_log_id: UUID = ...,
    request: schemas.FormDataAttachmentPresignedRequest = ...,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.get_form_data_attachment_presigned_url(
        complaint=complaint,
        incident_log_id=incident_log_id,
        request=request,
        current_user=current_user,
        db=db,
    )


@router.post(
    "/{complaint_id}/evidence/incident-log/form-data/{incident_log_id}/attachments/register",
    summary="INCIDENT_LOG 타입 사건 일지 '폼 데이터' 첨부 자료 등록 (복수 업로드 지원)",
    description="Presigned URL로 S3 업로드 완료 후 호출하세요. 썸네일/상세 이미지는 생성하지 않습니다.",
    response_model=schemas.FormDataAttachmentRegisterResponse,
    responses=evidence_errors.REGISTER_EVIDENCE_ERRORS_RESPONSES,
)
def register_form_data_attachments(
    complaint: Complaint = Depends(get_owned_complaint),
    incident_log_id: UUID = ...,
    request: schemas.FormDataAttachmentRegisterRequest = ...,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_incident_log_service.register_form_data_attachments(
        complaint=complaint,
        incident_log_id=incident_log_id,
        request=request,
        current_user=current_user,
        db=db,
    )


@router.delete(
    "/evidence/incident-log/form-data/{incident_log_id}/attachments",
    summary="INCIDENT_LOG 타입 사건 일지 '폼 데이터' 첨부 자료 삭제 (복수 삭제 지원)",
    description="INCIDENT_LOG 타입 사건 일지 폼 데이터 첨부 자료를 여러 건 삭제할 수 있습니다.",
    status_code=204,
    responses=INCIDENT_LOG_ACCESS_AND_TYPE_CHECK_RESPONSES,
)
def delete_form_data_attachments(
    incident_log_id: UUID,
    request: schemas.FormDataAttachmentDeleteRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence_incident_log_service.delete_form_data_attachments(
        incident_log_id=incident_log_id,
        attachment_ids=request.attachment_ids,
        current_user=current_user,
        db=db,
    )
