import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse


class EvidenceVictimRegisterItemResponse(BaseResponse):
    victim_id: UUID = Field(
        ...,
        description="피해 사진/영상 ID",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.mp4"])
    content_type: str = Field(..., description="Content-Type", examples=["video/mp4"])
    duration_seconds: int = Field(..., description="영상 길이(초)", examples=[123])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])


class EvidenceVictimRegisterListResponse(BaseResponse):
    items: list[EvidenceVictimRegisterItemResponse] = Field(
        ..., description="등록된 피해 사진/영상 목록"
    )


class EvidenceVictimOriginalResponse(BaseResponse):
    victim_id: UUID = Field(
        ...,
        description="피해 사진/영상 ID",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.mp4"])
    content_type: str = Field(..., description="Content-Type", examples=["video/mp4"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    duration_seconds: int = Field(..., description="영상 길이(초)", examples=[123])
    url: str = Field(..., description="원본 영상 URL", examples=["https://..."])
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


class EvidenceVictimPreviewResponse(BaseResponse):
    victim_id: UUID = Field(
        ...,
        description="피해 사진/영상 ID",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    duration_seconds: int = Field(..., description="영상 길이(초)", examples=[123])
    thumbnail_url: str = Field(..., description="썸네일 URL", examples=["https://..."])


class EvidenceVictimPreviewListResponse(BaseResponse):
    previews: list[EvidenceVictimPreviewResponse] = Field(
        ..., description="피해 사진/영상 프리뷰 목록"
    )
    total_count: int = Field(..., description="총 개수", examples=[10])


class EvidenceVictimDetailResponse(BaseResponse):
    victim_id: UUID = Field(
        ...,
        description="피해 사진/영상 ID",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    type: str = Field(..., description="파일 타입")
    filename: str = Field(..., description="파일명", examples=["evidence.mp4"])
    duration_seconds: int = Field(..., description="영상 길이(초)", examples=[123])
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
    thumbnail_url: str = Field(..., description="썸네일 URL", examples=["https://..."])


class EvidenceVictimDetailListResponse(BaseResponse):
    details: list[EvidenceVictimDetailResponse] = Field(..., description="피해 사진/영상 상세 목록")
    total_count: int = Field(..., description="총 개수", examples=[10])
