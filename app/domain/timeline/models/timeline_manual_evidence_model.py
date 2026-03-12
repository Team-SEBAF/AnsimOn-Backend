from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.base.base_db import Base


class TimelineManualEvidence(Base):
    """직접 추가 증거. AI 분석용 evidence_* 테이블이 아닌 타임라인 전용 저장."""

    __tablename__ = "timeline_manual_evidences"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    complaint_id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        ForeignKey("complaints.complaint_id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="file_type: IMAGE, AUDIO, VIDEO, DOCUMENT, ETC (content_type에서 파생, evidence_type 없음)",
    )
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="영상/음성 길이(초). 이미지/문서는 NULL",
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
