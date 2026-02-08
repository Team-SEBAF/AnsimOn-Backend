from uuid import UUID

from app.domain.evidence.repos.evidence_repository_base import EvidenceRepositoryBase

from ..models.evidence_tracking_model import EvidenceTracking


class EvidenceTrackingRepository(EvidenceRepositoryBase):
    model_class = EvidenceTracking
    pk_attr = "tracking_id"

    def get(self, tracking_id: UUID) -> EvidenceTracking | None:
        return super().get(tracking_id)

    def delete(self, tracking: EvidenceTracking) -> None:
        super().delete(tracking)
