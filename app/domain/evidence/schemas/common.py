"""Evidence 공통 스키마. presigned-url, form-data 첨부, Timeline 등에서 공유."""

from pydantic import Field

from app.base.base_request import BaseRequest


class EvidencePresignedUrlItemRequest(BaseRequest):
    """Presigned URL 발급 시 파일 항목. Evidence, form-data 첨부, Timeline 등에서 공통 사용."""

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
        description="파일 크기(바이트)",
        examples=[12345],
        ge=1,
    )
    duration_seconds: int | None = Field(
        None,
        description="영상/음성 길이(초). 해당 타입일 때 필수",
        examples=[120],
        ge=1,
    )
