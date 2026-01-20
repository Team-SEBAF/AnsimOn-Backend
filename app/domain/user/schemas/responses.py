from pydantic import Field

from app.base import BaseResponse

from .dtos import TokenDTO, UserDTO


class SignUpEmailResponse(BaseResponse, UserDTO):
    pass


class VerifyEmailResponse(BaseResponse):
    email: str = Field(..., description="이메일", examples=["user999@example.com"])
    email_verified: bool = Field(..., description="이메일 인증 여부", examples=[True])


class LoginEmailResponse(BaseResponse, TokenDTO):
    refresh_token: str = Field(
        ...,
        description="리프레시 토큰",
        examples=["eyJjdHkiOiJKV1Qi..."],
    )
    pass


class MeResponse(BaseResponse, UserDTO):
    pass


class RefreshTokenResponse(BaseResponse, TokenDTO):
    pass
