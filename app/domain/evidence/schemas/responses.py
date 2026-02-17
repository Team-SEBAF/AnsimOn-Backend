import datetime
from uuid import UUID

from pydantic import AwareDatetime, Field

from app.base.base_response import BaseResponse


class EvidencePresignedUrlItemResponse(BaseResponse):
    index: int = Field(..., description="요청 item의 index (요청-응답 매칭용)")
    filename: str = Field(..., description="파일명 (가독성용)", examples=["evidence.jpg"])
    url: str = Field(..., description="S3 PUT 업로드용 presigned URL")
    evidence_id: UUID = Field(
        ..., description="DB 저장 시 전달할 ID (타입별: message_id, voice_id 등)"
    )


class EvidencePresignedUrlResponse(BaseResponse):
    items: list[EvidencePresignedUrlItemResponse] = Field(
        ..., description="발급된 Presigned URL 목록"
    )


class EvidenceOriginalResponse(BaseResponse):
    """타입별 원본 파일 조회 공통 응답 (get_original용)."""

    evidence_id: UUID = Field(
        ...,
        description="증거 ID (타입별: message_id, voice_id 등)",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.jpg"])
    content_type: str = Field(..., description="Content-Type", examples=["image/jpeg"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    url: str = Field(..., description="원본 파일 presigned URL", examples=["https://..."])


class UpdateEvidenceFileNameResponse(BaseResponse):
    evidence_id: UUID = Field(
        ...,
        description="증거 ID (각 타입의 증거 ID, 예: message_id, voice_id, incident_log_id)",
        examples=[UUID("123e4567-e89b-12d3-a456-426614174000")],
    )
    filename: str = Field(..., description="증거 파일명", examples=["증거 이름"])
    updated_at: AwareDatetime = Field(
        ...,
        description="수정 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )
