from uuid import UUID

from app.domain.evidence.repos.evidence_repository_base import EvidenceRepositoryBase

from ..models.evidence_victim_model import EvidenceVictim


class EvidenceVictimRepository(EvidenceRepositoryBase):
    model_class = EvidenceVictim
    pk_attr = "victim_id"

    def get(self, victim_id: UUID) -> EvidenceVictim | None:
        return super().get(victim_id)

    def delete(self, victim: EvidenceVictim) -> None:
        super().delete(victim)
