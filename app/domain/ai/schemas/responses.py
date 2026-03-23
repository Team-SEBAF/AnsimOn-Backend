from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse


class TaskRequestResponse(BaseResponse):
    """AI 태스크 요청 응답"""

    task_id: UUID = Field(
        ...,
        description="생성된 태스크 ID",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )


class TimelineTaskIdResponse(BaseResponse):
    """현재(가장 최근) 타임라인 태스크 ID 응답"""

    task_id: UUID | None = Field(
        ...,
        description="가장 최근 타임라인 태스크 ID (없으면 null)",
    )


class TimelineNeedToGenerateResponse(BaseResponse):
    """타임라인 생성 필요 여부 응답 (최초 생성·재생성 모두 해당)"""

    need_to_generate: bool = Field(
        ...,
        description="타임라인 생성 필요 여부 (생성된 적 없거나 재생성 필요 시 True)",
    )
