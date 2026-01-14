from typing import Literal

from pydantic import Field

from app.base import BaseResponse

from .dtos import UserDTO


class SignUpEmailResponse(BaseResponse, UserDTO):
    pass


class VerifyEmailResponse(BaseResponse):
    email: str = Field(..., description="이메일", examples=["user999@example.com"])
    is_verified: bool = Field(..., description="이메일 인증 여부", examples=[True])


class LoginEmailResponse(BaseResponse):
    access_token: str = Field(
        ...,
        description="액세스 토큰 (JWT)",
        examples=["eyJraWQiOiJLT1pB..."],
    )
    id_token: str = Field(
        ...,
        description="ID 토큰 (JWT)",
        examples=["eyJraWQiOiJLT1pB..."],
    )
    refresh_token: str = Field(
        ...,
        description="리프레시 토큰",
        examples=["eyJjdHkiOiJKV1Qi..."],
    )
    expires_in: int = Field(
        ...,
        description="토큰 만료 시간 (초)",
        examples=[3600],
    )
    token_type: Literal["Bearer"] = Field(
        "Bearer",
        description="토큰 타입",
        examples=["Bearer"],
    )


class MeResponse(BaseResponse, UserDTO):
    pass
