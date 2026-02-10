from uuid import UUID

from app.domain.evidence.repos.evidence_repository_base import EvidenceRepositoryBase

from ..models.evidence_message_model import EvidenceMessage


class EvidenceMessageRepository(EvidenceRepositoryBase):
    model_class = EvidenceMessage
    pk_attr = "message_id"

    def get(self, message_id: UUID) -> EvidenceMessage | None:
        return super().get(message_id)

    def delete(self, message: EvidenceMessage) -> None:
        super().delete(message)
