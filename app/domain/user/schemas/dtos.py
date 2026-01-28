import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class UserDTO(BaseModel):
    user_sub: UUID = Field(
        ...,
        description="사용자 고유 식별자 (Cognito sub)",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    email: str = Field(..., description="이메일", examples=["user999@example.com"])
    email_verified: bool = Field(..., description="이메일 인증 여부", examples=[True])
    name: str = Field(..., description="이름", examples=["홍길동"])
    birthdate: datetime.date = Field(
        ..., description="생년월일 (YYYY-MM-DD)", examples=[datetime.date(2000, 1, 1)]
    )


class TokenDTO(BaseModel):
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
    expires_in: int = Field(
        ...,
        description="액세스 토큰 만료 시간 (초)",
        examples=[3600],
    )
    token_type: Literal["Bearer"] = Field(
        "Bearer",
        description="액세스 토큰 타입",
        examples=["Bearer"],
    )
