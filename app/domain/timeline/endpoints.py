from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.timeline import schemas
from app.domain.timeline.errors import GET_TIMELINE_ERRORS_RESPONSES
from app.domain.timeline.service import timeline_service

router = APIRouter(prefix="/api/v1", tags=["Timeline"])


@router.get(
    "/{complaint_id}/timeline",
    summary="타임라인 조회",
    description="날짜 > 시각 > 증거 계층 구조의 타임라인을 조회합니다. row 없으면 default insert.",
    response_model=schemas.TimelineResponse,
)
def get_timeline_api(
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
def get_timeline_evidences_api(
    complaint: Complaint = Depends(get_owned_complaint),
    timeline_evidence_id: UUID = ...,
    db: Session = Depends(get_db),
):
    return timeline_service.get_timeline_evidences(
        complaint.complaint_id,
        timeline_evidence_id,
        db,
    )
