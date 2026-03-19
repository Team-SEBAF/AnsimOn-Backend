from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.ai.schemas.responses import TaskRequestResponse
from app.domain.ai.service import ai_service
from app.domain.complaint import Complaint, get_owned_complaint

router = APIRouter(prefix="/api/v1", tags=["AI"])


@router.post(
    "/{complaint_id}/ai/request/generate-timeline",
    summary="타임라인 생성 요청 (아직 실행하지 말아주세요.)",
    description="타임라인 생성 요청을 보냅니다. 이 API에서는 생성 결과를 응답하지 않습니다. SSE 서버와 연결하여 결과 스트림을 확인하세요.",
    response_model=TaskRequestResponse,
)
def request_generate_timeline(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return ai_service.request_generate_timeline(complaint, db)
