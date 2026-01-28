import datetime

from pydantic import Field

from app.base.base_request import BaseRequest


class SignUpEmailRequest(BaseRequest):
    email: str = Field(..., description="이메일", examples=["user999@example.com"])
    password: str = Field(..., description="비밀번호", examples=["SecurePass123!"])
    name: str = Field(..., description="이름", examples=["홍길동"])
    birthdate: datetime.date = Field(
        ..., description="생년월일 (YYYY-MM-DD)", examples=[datetime.date(2000, 1, 1)]
    )


class VerifyEmailRequest(BaseRequest):
    email: str = Field(..., description="이메일", examples=["user999@example.com"])
    code: str = Field(..., description="인증 코드", examples=["123456"])


class ResendEmailVerificationRequest(BaseRequest):
    email: str = Field(..., description="이메일", examples=["user999@example.com"])


class LoginEmailRequest(BaseRequest):
    email: str = Field(..., description="이메일", examples=["user999@example.com"])
    password: str = Field(..., description="비밀번호", examples=["SecurePass123!"])


class UpdateMeRequest(BaseRequest):
    name: str | None = Field(None, description="이름", examples=["홍길동"])
    birthdate: datetime.date | None = Field(
        None, description="생년월일 (YYYY-MM-DD)", examples=[datetime.date(2000, 1, 1)]
    )


class RefreshTokenRequest(BaseRequest):
    id_token: str = Field(..., description="ID 토큰", examples=["eyJjdHkiOiJKV1Qi..."])
    refresh_token: str = Field(..., description="리프레시 토큰", examples=["eyJjdHkiOiJKV1Qi..."])
