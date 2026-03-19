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
