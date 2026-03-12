from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest
from app.domain.evidence.schemas.common import EvidencePresignedUrlItemRequest
from app.domain.timeline.constant import TimelineTag


class UpdateTimelineEvidenceRequest(BaseRequest):
    """타임라인 증거 메타데이터 수정 요청. date, time, title, description, tags."""

    date: str | None = Field(None, description="날짜 (YYYY-MM-DD)", examples=["2026-02-12"])
    time: str | None = Field(None, description="시각 HH:MM", examples=["11:30"])
    title: str | None = Field(None, description="제목", examples=["협박 문자 수신"])
    description: str | None = Field(
        None, description="설명", examples=["스토킹범으로부터 협박성 문자가 수신됨"]
    )
    tags: list[TimelineTag] | None = Field(
        None, description="태그", examples=[["REPEAT", "THREAT_COERCION"]]
    )


class ManualTimelineEvidenceFormDataUploadRequest(BaseRequest):
    """직접 추가 증거 생성 요청 (form-data)."""

    date: str = Field(..., description="날짜 (YYYY-MM-DD)", examples=["2026-02-12"])
    time: str = Field(..., description="시각 HH:MM", examples=["14:00"])
    title: str = Field(..., description="제목", examples=["추가 증거"])
    description: str = Field(..., description="설명", examples=["직접 촬영한 사진"])
    tags: list[TimelineTag] = Field(
        default_factory=list, description="태그", examples=[["REPEAT", "THREAT_COERCION"]]
    )


class ManualTimelineEvidencePresignedRequest(BaseRequest):
    """직접 추가 증거 Presigned URL 발급 요청. content_type 제한 없음."""

    items: list[EvidencePresignedUrlItemRequest] = Field(
        ...,
        min_length=1,
        description="업로드할 파일 목록",
    )


class ManualTimelineEvidenceRegisterItemRequest(BaseRequest):
    referenced_manual_evidence_id: UUID = Field(
        ...,
        description="Presigned URL 발급 시 받은 manual_evidence_id",
        examples=["a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.jpg"])


class ManualTimelineEvidenceRegisterRequest(BaseRequest):
    items: list[ManualTimelineEvidenceRegisterItemRequest] = Field(
        ...,
        min_length=1,
        description="등록할 직접 추가 증거 목록",
    )


class ReferencedManualEvidenceDeleteRequest(BaseRequest):
    referenced_manual_evidence_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="삭제할 참조 증거 ID 목록",
    )


class TimelineEvidenceDeleteRequest(BaseRequest):
    timeline_evidence_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="삭제할 타임라인 증거 ID 목록",
    )
