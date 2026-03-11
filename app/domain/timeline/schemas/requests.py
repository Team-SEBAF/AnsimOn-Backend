from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.evidence.schemas.common import EvidencePresignedUrlItemRequest
from app.domain.timeline.constant import TimelineTag


class UpdateTimelineEvidenceRequest(BaseModel):
    """타임라인 증거 메타데이터 수정 요청. date, time, title, description, tags."""

    date: str | None = Field(None, description="날짜 (YYYY-MM-DD)")
    time: str | None = Field(None, description="시각 HH:MM")
    title: str | None = Field(None, description="제목")
    description: str | None = Field(None, description="설명")
    tags: list[TimelineTag] | None = Field(None, description="태그")


class ManualEvidencePresignedRequest(BaseModel):
    """수동 증거 Presigned URL 발급 요청. content_type 제한 없음."""

    items: list[EvidencePresignedUrlItemRequest] = Field(
        ...,
        min_length=1,
        description="업로드할 파일 목록",
    )


class ManualEvidenceRegisterItemRequest(BaseModel):
    manual_evidence_id: UUID = Field(
        ..., description="Presigned URL 발급 시 받은 manual_evidence_id"
    )
    filename: str = Field(..., description="파일명")


class ManualEvidenceRegisterRequest(BaseModel):
    items: list[ManualEvidenceRegisterItemRequest] = Field(
        ...,
        min_length=1,
        description="등록할 수동 증거 목록",
    )
