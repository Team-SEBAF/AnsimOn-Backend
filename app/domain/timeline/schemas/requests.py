from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.evidence.schemas.common import EvidencePresignedUrlItemRequest
from app.domain.timeline.constant import TimelineTag


class UpdateTimelineEvidenceRequest(BaseModel):
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


class ManualTimelineEvidenceFormDataUploadRequest(BaseModel):
    """수동 증거 슬롯 생성 요청 (form-data)."""

    date: str = Field(..., description="날짜 (YYYY-MM-DD)", examples=["2026-02-12"])
    time: str = Field(..., description="시각 HH:MM", examples=["14:00"])
    title: str = Field(..., description="제목", examples=["추가 증거"])
    description: str = Field(..., description="설명", examples=["직접 촬영한 사진"])
    tags: list[TimelineTag] = Field(
        default_factory=list, description="태그", examples=[["REPEAT", "THREAT_COERCION"]]
    )


class ManualTimelineEvidencePresignedRequest(BaseModel):
    """수동 증거 Presigned URL 발급 요청. content_type 제한 없음."""

    items: list[EvidencePresignedUrlItemRequest] = Field(
        ...,
        min_length=1,
        description="업로드할 파일 목록",
        examples=[
            [
                {
                    "index": 0,
                    "filename": "evidence.jpg",
                    "content_type": "image/jpeg",
                    "size_bytes": 12345,
                },
            ]
        ],
    )


class ManualTimelineEvidenceRegisterItemRequest(BaseModel):
    manual_evidence_id: UUID = Field(
        ...,
        description="Presigned URL 발급 시 받은 manual_evidence_id",
        examples=["a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"],
    )
    filename: str = Field(..., description="파일명", examples=["evidence.jpg"])


class ManualTimelineEvidenceRegisterRequest(BaseModel):
    items: list[ManualTimelineEvidenceRegisterItemRequest] = Field(
        ...,
        min_length=1,
        description="등록할 수동 증거 목록",
        examples=[
            [
                {
                    "manual_evidence_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                    "filename": "evidence.jpg",
                },
            ]
        ],
    )
