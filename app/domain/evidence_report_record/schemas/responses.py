import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT


class EvidenceReportRecordResponse(BaseResponse):
    report_record_id: UUID = Field(
        ...,
        description="증거 신고・사건 일지 ID",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.pdf"])
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


class EvidenceReportRecordUploadResponse(BaseResponse):
    report_records: list[EvidenceReportRecordResponse] = Field(
        ..., description="업로드된 증거 신고・사건 일지 목록"
    )
    type_invalid_filenames: list[str] = Field(
        ...,
        description=f"가능한 신고・사건 일지 타입({EVIDENCE_DOCUMENT_RESTRICT.allowed_types})이 아니라 거절된 파일명 목록",
        examples=["evidence.pdf"],
    )
    count_invalid_filenames: list[str] = Field(
        ...,
        description=f"최대 개수 {EVIDENCE_DOCUMENT_RESTRICT.max_count}개를 초과하여 거절된 파일명 목록",
        examples=["evidence.mp3"],
    )
    size_invalid_filenames: list[str] = Field(
        ...,
        description=f"파일 크기가 {EVIDENCE_DOCUMENT_RESTRICT.max_size_bytes / 1024 / 1024}MB를 초과하여 거절된 파일명 목록",
        examples=["evidence.mp3"],
    )
