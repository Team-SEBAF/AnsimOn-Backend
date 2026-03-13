"""ZIP/PDF 다운로드용 임시 엔드포인트."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.timeline_download.service import timeline_download_service

router = APIRouter(prefix="/api/v1", tags=["Timeline Download"])


@router.get(
    "/{complaint_id}/timeline/download/preview",
    summary="[임시] 다운로드용 타임라인 JSON 미리보기",
    description="ZIP/PDF 생성에 사용할 전처리된 타임라인 JSON. evidences_numstring_s3_key_list 포함.",
)
def get_timeline_for_download_preview(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return timeline_download_service.get_timeline_for_download(
        complaint=complaint,
        db=db,
    )
