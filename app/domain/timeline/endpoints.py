from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.timeline import schemas
from app.domain.timeline.errors import GET_TIMELINE_ERRORS_RESPONSES
from app.domain.timeline.service import timeline_service

router = APIRouter(prefix="/api/v1", tags=["Timeline"])


@router.get(
    "/{complaint_id}/timeline",
    summary="타임라인 조회",
    description="날짜 > 시각 > 증거 계층 구조의 타임라인을 조회합니다. (row 없으면 default insert)",
    response_model=schemas.TimelineResponse,
)
def get_timeline(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return timeline_service.get_timeline(complaint.complaint_id, db)


@router.get(
    "/{complaint_id}/timeline/evidences/{timeline_evidence_id}",
    summary="타임라인 증거 상세 조회",
    description="timeline_evidence_id에 해당하는 타임라인 증거 메타데이터(날짜, 시각, 제목, 설명, 태그)와 original/manual 증거 목록을 조회합니다.",
    response_model=schemas.TimelineEvidenceDetailResponse,
    responses=GET_TIMELINE_ERRORS_RESPONSES,
)
def get_timeline_evidences(
    complaint: Complaint = Depends(get_owned_complaint),
    timeline_evidence_id: UUID = ...,
    db: Session = Depends(get_db),
):
    return timeline_service.get_timeline_evidences(
        complaint.complaint_id,
        timeline_evidence_id,
        db,
    )


@router.patch(
    "/{complaint_id}/timeline/evidences/{timeline_evidence_id}",
    summary="타임라인 증거 메타데이터 수정 (증거 수정, 삭제 X)",
    description="타임라인 증거의 날짜, 시각, 제목, 설명, 태그를 수정합니다.",
    response_model=schemas.TimelineEvidenceMetadataResponse,
    responses=GET_TIMELINE_ERRORS_RESPONSES,
)
def update_timeline_evidence(
    complaint: Complaint = Depends(get_owned_complaint),
    timeline_evidence_id: UUID = ...,
    request: schemas.UpdateTimelineEvidenceRequest = Body(...),
    db: Session = Depends(get_db),
):
    return timeline_service.update_timeline_evidence(
        complaint.complaint_id,
        timeline_evidence_id,
        request,
        db,
    )


@router.post(
    "/{complaint_id}/timeline/evidences/{timeline_evidence_id}/manual-evidences/presigned-url",
    summary="타임라인 수동 증거 Presigned URL 발급 (복수 업로드 지원)",
    description="API Gateway 용량 제한이 10MB이기 때문에, Presigned URL로 S3에 직접 업로드 후 register API를 호출합니다. content_type 제한 없음.",
    response_model=schemas.ManualEvidencePresignedResponse,
    responses=GET_TIMELINE_ERRORS_RESPONSES,
)
def get_manual_evidence_presigned_url(
    complaint: Complaint = Depends(get_owned_complaint),
    request: schemas.ManualEvidencePresignedRequest = Body(...),
):
    return timeline_service.get_manual_evidence_presigned_url(
        complaint=complaint,
        request=request,
    )


@router.post(
    "/{complaint_id}/timeline/evidences/{timeline_evidence_id}/manual-evidences/register",
    summary="타임라인 수동 증거 등록 (복수 업로드 지원)",
    description="Presigned URL로 S3 업로드 완료 후 호출하세요. image/video는 썸네일용 detail을 추출합니다.",
    response_model=schemas.ManualEvidenceRegisterResponse,
    responses=GET_TIMELINE_ERRORS_RESPONSES | evidence_errors.REGISTER_EVIDENCE_ERRORS_RESPONSES,
)
def register_manual_evidences(
    complaint: Complaint = Depends(get_owned_complaint),
    timeline_evidence_id: UUID = ...,
    request: schemas.ManualEvidenceRegisterRequest = Body(...),
    db: Session = Depends(get_db),
):
    return timeline_service.register_manual_evidences(
        complaint=complaint,
        timeline_evidence_id=timeline_evidence_id,
        request=request,
        db=db,
    )
