import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse


class EvidenceVoiceRegisterItemResponse(BaseResponse):
    voice_id: UUID = Field(
        ..., description="증거 음성 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="파일명", examples=["evidence.mp3"])
    content_type: str = Field(..., description="Content-Type", examples=["audio/mpeg"])
    duration_seconds: int = Field(..., description="음성 길이(초)", examples=[123])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])


class EvidenceVoiceRegisterListResponse(BaseResponse):
    items: list[EvidenceVoiceRegisterItemResponse] = Field(..., description="등록된 증거 음성 목록")


class EvidenceVoiceOriginalResponse(BaseResponse):
    voice_id: UUID = Field(
        ..., description="증거 음성 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="파일명", examples=["evidence.mp3"])
    content_type: str = Field(..., description="Content-Type", examples=["audio/mpeg"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    duration_seconds: int = Field(..., description="음성 길이(초)", examples=[123])
    url: str = Field(..., description="원본 음성 URL", examples=["https://..."])
    created_at: datetime.datetime = Field(
        ...,
        description="생성 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )
    updated_at: datetime.datetime = Field(
        ...,
        description="수정 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )


class EvidenceVoicePreviewResponse(BaseResponse):
    voice_id: UUID = Field(
        ..., description="증거 음성 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="파일명", examples=["evidence.mp3"])
    duration_seconds: int = Field(..., description="음성 길이(초)", examples=[123])


class EvidenceVoicePreviewListResponse(BaseResponse):
    previews: list[EvidenceVoicePreviewResponse] = Field(..., description="증거 음성 프리뷰 목록")
    total_count: int = Field(..., description="총 개수", examples=[10])


class EvidenceVoiceDetailResponse(BaseResponse):
    voice_id: UUID = Field(
        ..., description="증거 음성 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    type: str = Field(..., description="audio | image. duration_seconds > 0이면 audio, 0이면 image")
    filename: str = Field(..., description="파일명", examples=["evidence.mp3"])
    duration_seconds: int = Field(..., description="음성 길이(초)", examples=[123])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    created_at: datetime.datetime = Field(
        ...,
        description="생성 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )
    updated_at: datetime.datetime = Field(
        ...,
        description="수정 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )


class EvidenceVoiceDetailListResponse(BaseResponse):
    details: list[EvidenceVoiceDetailResponse] = Field(..., description="증거 음성 상세 목록")
    total_count: int = Field(..., description="총 개수", examples=[10])
