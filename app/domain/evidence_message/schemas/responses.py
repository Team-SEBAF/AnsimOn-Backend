import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse


class EvidenceMessageRegisterItemResponse(BaseResponse):
    message_id: UUID = Field(
        ..., description="증거 메시지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="파일명", examples=["evidence.jpg"])
    content_type: str = Field(..., description="Content-Type", examples=["image/jpeg"])
    width: int | None = Field(None, description="이미지 가로 픽셀", examples=[1024])
    height: int | None = Field(None, description="이미지 세로 픽셀", examples=[768])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])


class EvidenceMessageRegisterListResponse(BaseResponse):
    items: list[EvidenceMessageRegisterItemResponse] = Field(
        ..., description="등록된 증거 메시지 목록"
    )


class EvidenceMessageOriginalImageResponse(BaseResponse):
    message_id: UUID = Field(
        ..., description="증거 메시지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="파일명", examples=["evidence.jpg"])
    content_type: str = Field(..., description="Content-Type", examples=["image/jpeg"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    width: int | None = Field(None, description="이미지 가로 픽셀", examples=[1024])
    height: int | None = Field(None, description="이미지 세로 픽셀", examples=[768])
    url: str = Field(..., description="원본 이미지 URL", examples=["https://..."])
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


class EvidenceMessagePreviewResponse(BaseResponse):
    message_id: UUID = Field(
        ..., description="증거 메시지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    thumbnail_url: str = Field(..., description="썸네일 URL", examples=["https://..."])


class EvidenceMessagePreviewListResponse(BaseResponse):
    previews: list[EvidenceMessagePreviewResponse] = Field(
        ..., description="증거 메시지 프리뷰 목록"
    )
    total_count: int = Field(..., description="총 개수", examples=[10])


class EvidenceMessageDetailResponse(BaseResponse):
    message_id: UUID = Field(
        ..., description="증거 메시지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="파일명", examples=["evidence.jpg"])
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


class EvidenceMessageDetailListResponse(BaseResponse):
    details: list[EvidenceMessageDetailResponse] = Field(..., description="증거 메시지 상세 목록")
    total_count: int = Field(..., description="총 개수", examples=[10])
