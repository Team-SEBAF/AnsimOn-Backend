from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from app.domain.complaint.models.complaint_model import ComplaintStep


class ComplaintDTO(BaseModel):
    complaint_id: UUID = Field(
        ..., description="고소장 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    user_sub: str = Field(
        ...,
        description="사용자 고유 식별자 (Cognito sub)",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    name: str = Field(..., description="고소장 제목", examples=["고소장 제목"])
    step: ComplaintStep = Field(..., description="고소장 단계", examples=[ComplaintStep.EVIDENCE])
    created_at: datetime = Field(..., description="최초 생성 시각 (응답: YYYY-MM-DD HH:MM)")
    updated_at: datetime = Field(..., description="최종 수정 시각 (응답: YYYY-MM-DD HH:MM)")

    @field_serializer("created_at", "updated_at")
    def _serialize_datetime(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M")
