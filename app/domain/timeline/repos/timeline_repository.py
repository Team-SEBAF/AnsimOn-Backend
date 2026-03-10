from uuid import UUID

from app.base.base_repository import BaseRepository
from app.domain.timeline.models import Timeline, TimelineEvidence


class TimelineRepository(BaseRepository):
    model_class = Timeline
    pk_attr = "id"

    def get_by_complaint_id(self, complaint_id: UUID) -> Timeline | None:
        return self.db.query(Timeline).filter(Timeline.complaint_id == complaint_id).first()


class TimelineEvidenceRepository(BaseRepository):
    model_class = TimelineEvidence
    pk_attr = "id"

    def list_by_timeline_id(self, timeline_id: UUID) -> list[TimelineEvidence]:
        return (
            self.db.query(TimelineEvidence)
            .filter(TimelineEvidence.timeline_id == timeline_id)
            .order_by(TimelineEvidence.evidence_id, TimelineEvidence.index)
            .all()
        )

    def list_by_evidence_id(self, timeline_id: UUID, evidence_id: UUID) -> list[TimelineEvidence]:
        """evidence_id(timeline JSON id)에 해당하는 timeline_evidences 목록, index 순."""
        return (
            self.db.query(TimelineEvidence)
            .filter(
                TimelineEvidence.timeline_id == timeline_id,
                TimelineEvidence.evidence_id == evidence_id,
            )
            .order_by(TimelineEvidence.index)
            .all()
        )
