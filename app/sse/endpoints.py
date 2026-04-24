from fastapi import APIRouter, Depends

from app.core.auth import AuthUser, get_current_user
from app.sse.errors import SSE_URL_ERRORS_RESPONSES
from app.sse.schemas import SseServerUrlResponse
from app.sse.service import get_sse_server_url

router = APIRouter(prefix="/api/v1", tags=["SSE"])


@router.get(
    "/sse/server-url",
    summary="SSE 서버 베이스 URL 조회",
    description=(
        "프론트는 이 값을 전역에 저장한 뒤 SSE API 호출 시 prefix로 사용하면 됩니다. "
        "RUNNING 태스크가 없으면 503입니다."
    ),
    response_model=SseServerUrlResponse,
    responses=SSE_URL_ERRORS_RESPONSES,
)
def sse_server_url(_current_user: AuthUser = Depends(get_current_user)):
    return SseServerUrlResponse(base_url=get_sse_server_url())
