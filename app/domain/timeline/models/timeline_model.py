from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, delete, event
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
    """타임라인 증거. timeline JSON의 timeline_evidence_id와 연결.
    is_original_evidence=True: evidence_id → evidence_* 테이블
    is_original_evidence=False: manual_evidence_id → timeline_manual_evidences.id (FK)
    """

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
    timeline_evidence_id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        nullable=False,
        comment="timeline JSON 내 증거 그룹 id",
    )
    index: Mapped[int] = mapped_column(nullable=False, comment="원본 순서 1, 2, 3, ...")
    evidence_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        nullable=True,
        comment="evidence_* 테이블 id (is_original_evidence=True일 때)",
    )
    manual_evidence_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        ForeignKey("timeline_manual_evidences.id", ondelete="CASCADE"),
        nullable=True,
        comment="timeline_manual_evidences.id (is_original_evidence=False일 때)",
    )
    is_original_evidence: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="True: AI 분석 증거(evidence_*), False: 수동 추가(timeline_manual_evidences)",
    )
    evidence_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="MESSAGE, VICTIM, VOICE, REPORT_RECORD, INCIDENT_LOG (is_original_evidence=True일 때만)",
    )
    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="IMAGE, AUDIO, VIDEO, DOCUMENT, ETC (항상 존재)",
    )

    def get_evidence_id(self) -> UUID | None:
        """조회용 evidence id. is_original_evidence에 따라 evidence_id 또는 manual_evidence_id 반환."""
        return self.evidence_id if self.is_original_evidence else self.manual_evidence_id


def _delete_manual_evidence_on_timeline_evidence_delete(
    mapper, connection, target: "TimelineEvidence"
):
    """TimelineEvidence 삭제 시 연결된 TimelineManualEvidence도 함께 삭제 (timeline_json에서 제거 시)."""
    if target.manual_evidence_id is not None:
        from app.domain.timeline.models.timeline_manual_evidence_model import TimelineManualEvidence

        connection.execute(
            delete(TimelineManualEvidence).where(
                TimelineManualEvidence.id == target.manual_evidence_id
            )
        )


event.listen(TimelineEvidence, "after_delete", _delete_manual_evidence_on_timeline_evidence_delete)
