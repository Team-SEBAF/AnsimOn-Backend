from pydantic import BaseModel, Field

from app.domain.timeline.constant import TimelineTag


class UpdateTimelineEvidenceRequest(BaseModel):
    """타임라인 증거 메타데이터 수정 요청. date, time, title, description, tags."""

    date: str | None = Field(None, description="날짜 (YYYY-MM-DD)")
    time: str | None = Field(None, description="시각 HH:MM")
    title: str | None = Field(None, description="제목")
    description: str | None = Field(None, description="설명")
    tags: list[TimelineTag] | None = Field(None, description="태그")
