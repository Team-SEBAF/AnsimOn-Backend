from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.timeline import schemas
from app.domain.timeline.errors import (
    GET_TIMELINE_ERRORS_RESPONSES,
    MANUAL_TIMELINE_EVIDENCE_RESPONSES,
)
from app.domain.timeline.service import timeline_service

router = APIRouter(prefix="/api/v1", tags=["Timeline"])


@router.get(
    "/{complaint_id}/timeline",
    summary="타임라인 조회",
    description="날짜 > 시각 > 증거 계층 구조의 타임라인을 조회합니다. (row 없으면 default insert)",
    response_model=schemas.TimelineResponse,
    responses=GET_TIMELINE_ERRORS_RESPONSES,
)
def get_timeline(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return timeline_service.get_timeline(complaint.complaint_id, db)


@router.get(
    "/{complaint_id}/timeline/evidences/{timeline_evidence_id}",
    summary="타임라인 증거 상세 조회",
    description="timeline_evidence_id에 해당하는 타임라인 증거 메타데이터(날짜, 시각, 제목, 설명, 태그)와 증거 목록을 조회합니다.",
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
    "/{complaint_id}/timeline/evidences/{timeline_evidence_id}/form-data",
    summary="타임라인 증거의 '폼 데이터'를 수정",
    description="타임라인 증거의 '폼 데이터'를 수정합니다. (증거 수정, 삭제 X)",
    response_model=schemas.TimelineEvidenceMetadataResponse,
)
def update_timeline_evidence_form_data(
    complaint: Complaint = Depends(get_owned_complaint),
    timeline_evidence_id: UUID = ...,
    request: schemas.UpdateTimelineEvidenceRequest = Body(...),
    db: Session = Depends(get_db),
):
    return timeline_service.update_timeline_evidence_form_data(
        complaint.complaint_id,
        timeline_evidence_id,
        request,
        db,
    )


@router.delete(
    "/{complaint_id}/timeline/evidences",
    summary="타임라인 증거 삭제 (복수 삭제 지원)",
    description="타임라인 증거를 여러 건 삭제할 수 있습니다.",
    status_code=204,
    responses=GET_TIMELINE_ERRORS_RESPONSES,
)
def delete_timeline_evidences(
    complaint: Complaint = Depends(get_owned_complaint),
    request: schemas.TimelineEvidenceDeleteRequest = Body(...),
    db: Session = Depends(get_db),
):
    timeline_service.delete_timeline_evidences(
        complaint=complaint,
        timeline_evidence_ids=request.timeline_evidence_ids,
        db=db,
    )


@router.post(
    "/{complaint_id}/timeline/evidences/manual/form-data",
    summary="타임라인 '직접 추가 증거'의 '폼 데이터'를 업로드",
    description="타임라인 증거의 '폼 데이터'를 업로드합니다. 참조 증거 추가는 별도 API를 사용합니다.",
    response_model=schemas.ManualTimelineEvidenceFormDataResponse,
)
def upload_manual_timeline_evidence_form_data(
    complaint: Complaint = Depends(get_owned_complaint),
    request: schemas.ManualTimelineEvidenceFormDataUploadRequest = Body(...),
    db: Session = Depends(get_db),
):
    return timeline_service.upload_manual_timeline_evidence_form_data(
        complaint.complaint_id,
        request,
        db,
    )


@router.post(
    "/{complaint_id}/timeline/evidences/{timeline_evidence_id}/manual/referenced-evidences/presigned-url",
    summary="타임라인 '직접 추가 증거'의 '참조 증거' Presigned URL 발급 (복수 업로드 지원)",
    description="API Gateway 용량 제한이 10MB이기 때문에, Presigned URL로 S3에 직접 업로드 후 register API를 호출합니다. 타입 제한 없음.",
    response_model=schemas.ReferencedManualEvidencePresignedResponse,
    responses=MANUAL_TIMELINE_EVIDENCE_RESPONSES,
)
def get_referenced_manual_evidence_presigned_url(
    complaint: Complaint = Depends(get_owned_complaint),
    timeline_evidence_id: UUID = ...,
    request: schemas.ManualTimelineEvidencePresignedRequest = Body(...),
    db: Session = Depends(get_db),
):
    return timeline_service.get_referenced_manual_evidence_presigned_url(
        complaint=complaint,
        timeline_evidence_id=timeline_evidence_id,
        request=request,
        db=db,
    )


@router.post(
    "/{complaint_id}/timeline/evidences/{timeline_evidence_id}/manual/referenced-evidences/register",
    summary="타임라인 '직접 추가 증거'의 '참조 증거'를 등록 (복수 업로드 지원)",
    description="Presigned URL로 S3 업로드 완료 후 호출하세요. image/video는 썸네일 사진을 추출합니다.",
    response_model=schemas.ReferencedManualEvidenceRegisterResponse,
    responses=MANUAL_TIMELINE_EVIDENCE_RESPONSES,
)
def register_referenced_manual_evidences(
    complaint: Complaint = Depends(get_owned_complaint),
    timeline_evidence_id: UUID = ...,
    request: schemas.ManualTimelineEvidenceRegisterRequest = Body(...),
    db: Session = Depends(get_db),
):
    return timeline_service.register_referenced_manual_evidences(
        complaint=complaint,
        timeline_evidence_id=timeline_evidence_id,
        request=request,
        db=db,
    )


@router.delete(
    "/{complaint_id}/timeline/evidences/{timeline_evidence_id}/manual/referenced-evidences",
    summary="타임라인 '직접 추가 증거'의 '참조 증거' 삭제 (복수 삭제 지원)",
    description="타임라인 직접 추가 증거의 참조 증거를 여러 건 삭제할 수 있습니다.",
    status_code=204,
    responses=MANUAL_TIMELINE_EVIDENCE_RESPONSES,
)
def delete_referenced_manual_evidences(
    complaint: Complaint = Depends(get_owned_complaint),
    timeline_evidence_id: UUID = ...,
    request: schemas.ReferencedManualEvidenceDeleteRequest = Body(...),
    db: Session = Depends(get_db),
):
    timeline_service.delete_referenced_manual_evidences(
        complaint=complaint,
        timeline_evidence_id=timeline_evidence_id,
        referenced_manual_evidence_ids=request.referenced_manual_evidence_ids,
        db=db,
    )
