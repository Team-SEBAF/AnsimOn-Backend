import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse
from app.domain.evidence.constant import EVIDENCE_TRACKING_RESTRICT


class EvidenceTrackingResponse(BaseResponse):
    tracking_id: UUID = Field(
        ..., description="증거 추적 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
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


class EvidenceTrackingUploadResponse(BaseResponse):
    trackings: list[EvidenceTrackingResponse] = Field(..., description="업로드된 증거 추적 목록")
    type_invalid_filenames: list[str] = Field(
        ...,
        description=f"가능한 영상 타입({EVIDENCE_TRACKING_RESTRICT.allowed_types})이 아니라 거절된 파일명 목록",
        examples=["evidence.pdf"],
    )
    count_invalid_filenames: list[str] = Field(
        ...,
        description=f"최대 개수 {EVIDENCE_TRACKING_RESTRICT.max_count}개를 초과하여 거절된 파일명 목록",
        examples=["evidence.mp4"],
    )
    size_invalid_filenames: list[str] = Field(
        ...,
        description=f"파일 크기가 {EVIDENCE_TRACKING_RESTRICT.max_size_bytes / 1024 / 1024}MB를 초과하여 거절된 파일명 목록",
        examples=["evidence.mp4"],
    )
    duration_invalid_filenames: list[str] = Field(
        ...,
        description=f"영상 길이가 {EVIDENCE_TRACKING_RESTRICT.max_duration_seconds}초를 초과하여 거절된 파일명 목록",
        examples=["evidence.mp4"],
    )


class EvidenceTrackingOriginalResponse(BaseResponse):
    tracking_id: UUID = Field(
        ..., description="증거 추적 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="파일명", examples=["evidence.mp4"])
    content_type: str = Field(..., description="Content-Type", examples=["video/mp4"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    duration_seconds: int = Field(..., description="영상 길이(초)", examples=[123])
    url: str = Field(..., description="원본 영상 URL", examples=["https://..."])


class EvidenceTrackingPreviewResponse(BaseResponse):
    tracking_id: UUID = Field(
        ..., description="증거 추적 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    duration_seconds: int = Field(..., description="영상 길이(초)", examples=[123])
    thumbnail_url: str = Field(..., description="썸네일 URL", examples=["https://..."])


class EvidenceTrackingPreviewListResponse(BaseResponse):
    previews: list[EvidenceTrackingPreviewResponse] = Field(
        ..., description="증거 추적 프리뷰 목록"
    )
    total_count: int = Field(..., description="총 개수", examples=[10])
