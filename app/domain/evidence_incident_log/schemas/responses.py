import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence_incident_log.models.evidence_incident_log_model import (
    EvidenceIncidentLogType,
)
from app.domain.evidence_incident_log.schemas.dtos import EvidenceIncidentLogFormDataDTO


class EvidenceIncidentLogFileResponse(BaseResponse):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="사건 일지 파일명", examples=["사건 일지 파일명"])
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


class EvidenceIncidentLogFileUploadResponse(BaseResponse):
    incident_log_files: list[EvidenceIncidentLogFileResponse] = Field(
        ..., description="업로드된 사건 일지 파일 목록"
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


class EvidenceIncidentLogFileOriginalResponse(BaseResponse):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="사건 일지 파일명", examples=["사건 일지 파일명"])
    content_type: str = Field(..., description="Content-Type", examples=["application/pdf"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    url: str = Field(..., description="원본 사건 일지 파일 URL", examples=["https://..."])


class EvidenceIncidentLogPreviewResponse(BaseResponse):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    type: EvidenceIncidentLogType = Field(
        ..., description="사건 일지 타입", examples=[EvidenceIncidentLogType.FILE]
    )
    filename: str = Field(..., description="사건 일지 파일명", examples=["사건 일지 파일명"])
    size_bytes: int | None = Field(
        ..., description="파일 크기(바이트), 폼데이터면 None", examples=[12345, None]
    )


class EvidenceIncidentLogPreviewListResponse(BaseResponse):
    previews: list[EvidenceIncidentLogPreviewResponse] = Field(
        ..., description="사건 일지 파일 프리뷰 목록"
    )
    total_count: int = Field(..., description="총 개수", examples=[10])


class EvidenceIncidentLogDetailResponse(BaseResponse):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    type: EvidenceIncidentLogType = Field(
        ..., description="사건 일지 타입", examples=[EvidenceIncidentLogType.FILE]
    )
    filename: str = Field(..., description="사건 일지 파일명", examples=["사건 일지 파일명"])
    size_bytes: int | None = Field(
        None, description="파일 크기(바이트), 폼데이터면 None", examples=[12345, None]
    )
    content_type: str | None = Field(
        None, description="Content-Type, 폼데이터면 None", examples=["application/pdf", None]
    )
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


class EvidenceIncidentLogDetailListResponse(BaseResponse):
    details: list[EvidenceIncidentLogDetailResponse] = Field(..., description="사건 일지 상세 목록")
    total_count: int = Field(..., description="총 개수", examples=[10])


class EvidenceIncidentLogFormDataResponse(BaseResponse, EvidenceIncidentLogFormDataDTO):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
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
