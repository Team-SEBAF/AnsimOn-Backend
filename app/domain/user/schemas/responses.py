import datetime
from uuid import UUID

from pydantic import AwareDatetime, Field

from app.base import BaseResponse


class SignUpEmailResponse(BaseResponse):
    user_sub: UUID = Field(
        ...,
        description="사용자 고유 식별자 (Cognito sub)",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    email: str = Field(..., description="이메일", examples=["user999@example.com"])
    is_verified: bool = Field(..., description="이메일 인증 여부", examples=[True])
    name: str = Field(..., description="이름", examples=["홍길동"])
    birthdate: datetime.date = Field(
        ..., description="생년월일 (YYYY-MM-DD)", examples=[datetime.date(2000, 1, 1)]
    )
    is_legal_representative: bool = Field(..., description="법정 대리인인지 여부", examples=[False])
    created_at: AwareDatetime = Field(
        ...,
        description="생성 시간 (ISO 8601, timezone-aware)",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )


class VerifyEmailResponse(BaseResponse):
    email: str = Field(..., description="이메일", examples=["user999@example.com"])
    is_verified: bool = Field(..., description="이메일 인증 여부", examples=[True])
