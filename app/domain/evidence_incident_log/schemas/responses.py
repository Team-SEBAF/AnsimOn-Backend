import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse
from app.domain.evidence_incident_log.constant import FormDataAttachmentType
from app.domain.evidence_incident_log.models.evidence_incident_log_model import (
    EvidenceIncidentLogType,
)
from app.domain.evidence_incident_log.schemas.dtos import EvidenceIncidentLogFormDataDTO


class EvidenceIncidentLogFileRegisterItemResponse(BaseResponse):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="사건 일지 파일명", examples=["사건 일지 파일명"])
    content_type: str = Field(..., description="Content-Type", examples=["application/pdf"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])


class EvidenceIncidentLogFileRegisterListResponse(BaseResponse):
    items: list[EvidenceIncidentLogFileRegisterItemResponse] = Field(
        ..., description="등록된 사건 일지 파일 목록"
    )


class EvidenceIncidentLogFileOriginalResponse(BaseResponse):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="사건 일지 파일명", examples=["사건 일지 파일명"])
    content_type: str = Field(..., description="Content-Type", examples=["application/pdf"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    url: str = Field(..., description="원본 사건 일지 파일 URL", examples=["https://..."])
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


class FormDataAttachmentResponse(BaseResponse):
    """form-data GET 시 첨부 자료 항목. DB metadata만 반환."""

    attachment_id: UUID = Field(..., description="첨부 자료 ID")
    type: FormDataAttachmentType = Field(
        ..., description="미디어 타입 (IMAGE/VIDEO/AUDIO/DOCUMENT/ETC)"
    )
    filename: str = Field(..., description="파일명")
    content_type: str = Field(..., description="Content-Type")
    size_bytes: int = Field(..., description="파일 크기(바이트)")
    duration_seconds: int | None = Field(None, description="영상/음성 길이(초)")
    created_at: datetime.datetime = Field(..., description="생성 시간")


class EvidenceIncidentLogFormDataResponse(BaseResponse, EvidenceIncidentLogFormDataDTO):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    attachments: list[FormDataAttachmentResponse] = Field(
        default_factory=list,
        description="첨부 자료 목록",
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


class FormDataAttachmentPresignedItemResponse(BaseResponse):
    index: int = Field(..., description="요청 item의 index")
    filename: str = Field(..., description="파일명")
    url: str = Field(..., description="S3 PUT 업로드용 presigned URL")
    attachment_id: UUID = Field(..., description="DB 저장 시 전달할 ID")


class FormDataAttachmentPresignedResponse(BaseResponse):
    items: list[FormDataAttachmentPresignedItemResponse] = Field(
        ..., description="발급된 Presigned URL 목록"
    )


class FormDataAttachmentRegisterItemResponse(BaseResponse):
    attachment_id: UUID = Field(..., description="첨부 자료 ID")
    type: FormDataAttachmentType = Field(
        ..., description="미디어 타입 (IMAGE/VIDEO/AUDIO/DOCUMENT/ETC)"
    )
    filename: str = Field(..., description="파일명")
    content_type: str = Field(..., description="Content-Type")
    size_bytes: int = Field(..., description="파일 크기(바이트)")
    duration_seconds: int | None = Field(None, description="영상/음성 길이(초)")


class FormDataAttachmentRegisterResponse(BaseResponse):
    items: list[FormDataAttachmentRegisterItemResponse] = Field(
        ..., description="등록된 첨부 자료 목록"
    )
