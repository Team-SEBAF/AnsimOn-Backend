import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse


class EvidenceReportRecordRegisterItemResponse(BaseResponse):
    report_record_id: UUID = Field(
        ...,
        description="증거 신고・사건 일지 ID",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.pdf"])
    content_type: str = Field(..., description="Content-Type", examples=["application/pdf"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])


class EvidenceReportRecordRegisterListResponse(BaseResponse):
    items: list[EvidenceReportRecordRegisterItemResponse] = Field(
        ..., description="등록된 신고・사건 일지 목록"
    )


class EvidenceReportRecordOriginalResponse(BaseResponse):
    report_record_id: UUID = Field(
        ...,
        description="증거 신고・사건 일지 ID",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.pdf"])
    content_type: str = Field(..., description="Content-Type", examples=["application/pdf"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    url: str = Field(..., description="원본 신고・사건 일지 URL", examples=["https://..."])
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


class EvidenceReportRecordPreviewResponse(BaseResponse):
    report_record_id: UUID = Field(
        ...,
        description="증거 신고・사건 일지 ID",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.pdf"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])


class EvidenceReportRecordPreviewListResponse(BaseResponse):
    previews: list[EvidenceReportRecordPreviewResponse] = Field(
        ..., description="증거 신고・사건 일지 프리뷰 목록"
    )
    total_count: int = Field(..., description="총 개수", examples=[10])


class EvidenceReportRecordDetailResponse(BaseResponse):
    report_record_id: UUID = Field(
        ...,
        description="증거 신고・사건 일지 ID",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.pdf"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    content_type: str = Field(..., description="Content-Type", examples=["application/pdf"])
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


class EvidenceReportRecordDetailListResponse(BaseResponse):
    details: list[EvidenceReportRecordDetailResponse] = Field(
        ..., description="증거 신고・사건 일지 상세 목록"
    )
    total_count: int = Field(..., description="총 개수", examples=[10])
