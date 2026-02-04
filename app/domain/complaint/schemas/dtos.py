import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

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
    created_at: AwareDatetime = Field(
        ...,
        description="생성 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )
    updated_at: AwareDatetime = Field(
        ...,
        description="수정 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )
