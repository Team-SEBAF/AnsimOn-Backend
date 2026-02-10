import datetime
from uuid import UUID

from pydantic import AwareDatetime, Field

from app.base.base_response import BaseResponse


class UpdateEvidenceFileNameResponse(BaseResponse):
    id: UUID = Field(
        ...,
        description="증거 ID (각 타입의 증거 ID, 예: message_id, voice_id, incident_log_id)",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="증거 파일명", examples=["증거 이름"])
    updated_at: AwareDatetime = Field(
        ...,
        description="수정 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )
