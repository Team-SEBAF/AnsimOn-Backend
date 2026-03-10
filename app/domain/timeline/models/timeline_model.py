from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_db import Base


class Timeline(Base):
    __tablename__ = "timelines"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    complaint_id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        ForeignKey("complaints.complaint_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    timeline_json: Mapped[dict] = mapped_column(JSONB, nullable=False)


class TimelineEvidence(Base):
    """타임라인 증거 원본. timeline JSON의 evidence_id와 연결."""

    __tablename__ = "timeline_evidences"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    timeline_id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        ForeignKey("timelines.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        nullable=False,
        comment="timeline JSON 내 증거 id",
    )
    index: Mapped[int] = mapped_column(nullable=False, comment="원본 순서 1, 2, 3, ...")
    original_id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        nullable=False,
        comment="evidence_victims, evidence_messages 등 실제 증거 테이블의 id",
    )
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="MESSAGE, VICTIM, VOICE, REPORT_RECORD, INCIDENT_LOG",
    )
