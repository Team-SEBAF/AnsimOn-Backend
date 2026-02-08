from uuid import UUID

from app.domain.evidence.repos.evidence_repository_base import EvidenceRepositoryBase

from ..models.evidence_voice_model import EvidenceVoice


class EvidenceVoiceRepository(EvidenceRepositoryBase):
    model_class = EvidenceVoice
    pk_attr = "voice_id"

    def get(self, voice_id: UUID) -> EvidenceVoice | None:
        return super().get(voice_id)

    def delete(self, voice: EvidenceVoice) -> None:
        super().delete(voice)
