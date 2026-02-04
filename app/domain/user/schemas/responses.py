import datetime
from uuid import UUID

from pydantic import AwareDatetime, Field

from app.base.base_response import BaseResponse

from .dtos import TokenDTO, UserDTO


class SignUpEmailResponse(BaseResponse, UserDTO):
    pass


class VerifyEmailResponse(BaseResponse):
    email: str = Field(..., description="이메일", examples=["user999@example.com"])
    email_verified: bool = Field(..., description="이메일 인증 여부", examples=[True])


class LoginTokenResponse(BaseResponse, TokenDTO):
    refresh_token: str = Field(
        ...,
        description="리프레시 토큰",
        examples=["eyJjdHkiOiJKV1Qi..."],
    )
    pass


class MeResponse(BaseResponse, UserDTO):
    created_at: AwareDatetime = Field(
        ...,
        description="생성 시간 (ISO 8601, timezone-aware)",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )
    complaint_id: UUID = Field(
        ..., description="고소장 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    pass


class RefreshTokenResponse(BaseResponse, TokenDTO):
    pass
