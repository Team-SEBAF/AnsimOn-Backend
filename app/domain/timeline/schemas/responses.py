from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse
from app.domain.timeline.constant import TimelineTag


class TimelineEvidenceResponse(BaseResponse):
    """타임라인 증거 항목. 시각이 겹칠 때 index로 정렬."""

    id: UUID = Field(..., description="증거 ID")
    index: int = Field(..., description="동일 시각 내 정렬 순서 (1, 2, 3, ...)")
    title: str = Field(..., description="제목")
    description: str = Field(..., description="설명")
    tags: list[TimelineTag] = Field(
        default_factory=list,
        description="태그 (REPEAT, PHYSICAL_HARM, THREAT_COERCION, SEXUAL_INSULT, REFUSAL_INTENT)",
    )
    referenced_evidence_count: int = Field(
        ..., description="참조 증거 원본 수 (썸네일 오버레이 숫자)"
    )
    has_thumbnail: bool = Field(
        ...,
        description="썸네일 여부. True면 첫 번째 이미지/영상 원본의 썸네일 사용",
    )
    thumbnail_url: str = Field(
        default="",
        description="썸네일 URL. has_thumbnail True일 때 S3 path로 생성 (추후 구현)",
    )
    duration_seconds: int | None = Field(
        None,
        description="영상/음성 길이(초)",
    )


class TimelineEventResponse(BaseResponse):
    """타임라인 이벤트. 시각 + 해당 시각의 증거 목록."""

    time: str = Field(..., description="시각 HH:MM (예: 11:30, 17:00)")
    evidences: list[TimelineEvidenceResponse] = Field(
        default_factory=list,
        description="해당 시각의 증거 목록. 시각 기준 정렬 후 id 기준 2차 정렬",
    )


class TimelineDateGroupResponse(BaseResponse):
    """날짜별 타임라인 그룹."""

    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    events: list[TimelineEventResponse] = Field(
        default_factory=list,
        description="해당 날짜의 이벤트 목록. 시각 기준 정렬",
    )


class TimelineResponse(BaseResponse):
    """타임라인 전체 응답. 날짜 > 시각 > 증거 계층 구조."""

    items: list[TimelineDateGroupResponse] = Field(
        default_factory=list,
        description="날짜별 타임라인 그룹 목록",
    )
