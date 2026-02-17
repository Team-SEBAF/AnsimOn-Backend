from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest
from app.domain.evidence.constant import EvidenceType


class EvidencePresignedUrlItemRequest(BaseRequest):
    index: int = Field(
        ...,
        description="클라이언트 식별용 인덱스. 검증 실패 시 failed_index_list에 그대로 반환",
        examples=[0],
        ge=0,
    )
    filename: str = Field(
        ..., description="파일명 (가독성용, 식별자는 index)", examples=["evidence.jpg"]
    )
    content_type: str = Field(
        ..., description="Content-Type (S3 시그니처에 필요)", examples=["image/jpeg"]
    )
    size_bytes: int = Field(
        ...,
        description="파일 크기(바이트). 타입별 max_size_bytes 제한 적용",
        examples=[12345],
        ge=1,
    )
    duration_seconds: int | None = Field(
        None,
        description="영상/음성 길이(초). VOICE, TRACKING 타입일 때 필수. 타입별 max_duration_seconds 제한 적용",
        examples=[120],
        ge=1,
    )


class EvidencePresignedUrlRequest(BaseRequest):
    """복수 업로드 지원. 한 요청당 한 타입만. items에 여러 개 넣으면 한 번에 presigned URL 발급."""

    type: EvidenceType = Field(
        ...,
        description="증거 타입 (한 요청당 한 타입만)",
        examples=[EvidenceType.MESSAGE],
    )
    items: list[EvidencePresignedUrlItemRequest] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="발급할 presigned URL 목록 (타입별 max_count 제한 적용)",
    )


class UpdateEvidenceFilenameRequest(BaseRequest):
    type: EvidenceType = Field(
        ...,
        description="증거 타입",
        examples=[EvidenceType.MESSAGE],
    )
    filename: str = Field(..., description="새 파일명", examples=["증거_이미지"])


class DeleteEvidenceRequest(BaseRequest):
    type: EvidenceType = Field(
        ...,
        description="증거 타입 (한 요청당 한 타입만)",
        examples=[EvidenceType.MESSAGE],
    )
    evidence_ids: list[UUID] = Field(
        ...,
        description="삭제할 증거 ID 목록 (해당 타입의 ID, 예: message_id, voice_id)",
        min_length=1,
        examples=[[UUID("123e4567-e89b-12d3-a456-426614174000")]],
    )
