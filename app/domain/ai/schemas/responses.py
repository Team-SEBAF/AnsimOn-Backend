from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse


class TaskIdResponse(BaseResponse):
    """AI 태스크 ID 응답 (생성 요청·현재 태스크 조회 공통)."""

    task_id: UUID | None = Field(
        ...,
        description="태스크 ID. 생성 요청 시 항상 UUID, 현재 태스크 조회 시 없으면 null",
    )


class NeedToGenerateResponse(BaseResponse):
    need_to_generate: bool = Field(..., description="생성 필요 여부")
