from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.ai.errors import CURRENT_TASK_ERRORS_RESPONSES
from app.domain.ai.models import LLMType
from app.domain.ai.schemas.responses import (
    NeedToGenerateResponse,
    TaskRequestResponse,
    TimelineTaskIdResponse,
)
from app.domain.ai.service import ai_service
from app.domain.complaint import Complaint, get_owned_complaint

router = APIRouter(prefix="/api/v1", tags=["AI"])


@router.get(
    "/{complaint_id}/ai/timeline/need-to-generate",
    summary="타임라인 생성 필요 여부 조회",
    description="타임라인 생성 필요 여부를 조회합니다. 생성된 적 없거나 재생성 필요 시 True를 반환합니다. Step 02로 넘어갈 때 확인해 주세요.",
    response_model=NeedToGenerateResponse,
)
def get_need_to_generate(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return ai_service.get_need_to_generate(complaint.complaint_id, db)


@router.get(
    "/{complaint_id}/ai/timeline/current-task-id",
    summary="현재 타임라인 생성 요청 중인 태스크 ID 조회",
    description="현재 타임라인 생성 요청 중인 태스크 ID를 조회합니다. 생성 도중 재접속 시 확인할 때 사용합니다.",
    response_model=TimelineTaskIdResponse,
    responses=CURRENT_TASK_ERRORS_RESPONSES,
)
def get_current_timeline_task_id(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return ai_service.get_current_timeline_task_id(complaint, db)


@router.post(
    "/{complaint_id}/ai/timeline/request/generate",
    summary="타임라인 생성 요청",
    description="타임라인 생성 요청을 보냅니다. 이 API에서는 생성 결과를 응답하지 않습니다. SSE 서버와 연결하여 결과 스트림을 확인하세요.",
    response_model=TaskRequestResponse,
)
def request_generate_timeline(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
    llm_type: LLMType = Query(..., description="mock 또는 openAI"),
):
    return ai_service.request_generate_timeline(complaint, db, llm_type)


@router.get(
    "/{complaint_id}/ai/document/need-to-generate",
    summary="고소장/진술서 생성 필요 여부 조회",
    description="고소장/진술서 생성 필요 여부 조회합니다. 생성된 적 없거나 재생성 필요 시 True를 반환합니다. Step 03로 넘어갈 때 확인해 주세요.",
    response_model=NeedToGenerateResponse,
)
def get_document_need_to_generate(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return ai_service.get_document_need_to_generate(complaint.complaint_id, db)
