from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.timeline import schemas
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
