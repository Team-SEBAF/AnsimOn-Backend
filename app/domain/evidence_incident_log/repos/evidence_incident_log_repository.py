from uuid import UUID

from app.base.base_repository import BaseRepository
from app.domain.evidence.repos.evidence_repository_base import EvidenceRepositoryBase

from ..models.evidence_incident_log_model import (
    EvidenceIncidentLog,
    EvidenceIncidentLogFile,
    EvidenceIncidentLogFormData,
)


class EvidenceIncidentLogRepository(EvidenceRepositoryBase):
    model_class = EvidenceIncidentLog
    pk_attr = "incident_log_id"

    def get(self, incident_log_id: UUID) -> EvidenceIncidentLog | None:
        return super().get(incident_log_id)

    def update(
        self, incident_log: EvidenceIncidentLog, values: dict[str, object]
    ) -> EvidenceIncidentLog:
        for key, value in values.items():
            if not hasattr(incident_log, key):
                raise ValueError(f"Invalid field: {key}")
            setattr(incident_log, key, value)
        return incident_log

    def delete(self, incident_log: EvidenceIncidentLog) -> None:
        super().delete(incident_log)


class EvidenceIncidentLogFileRepository(BaseRepository):
    model_class = EvidenceIncidentLogFile
    pk_attr = "incident_log_id"

    def get(self, incident_log_id: UUID) -> EvidenceIncidentLogFile | None:
        return super().get(incident_log_id)

    def list_by_incident_log_ids(
        self, incident_log_ids: list[UUID]
    ) -> list[EvidenceIncidentLogFile]:
        return (
            self.db.query(self.model_class)
            .filter(self.model_class.incident_log_id.in_(incident_log_ids))
            .all()
        )

    def delete(self, incident_log_file: EvidenceIncidentLogFile) -> None:
        super().delete(incident_log_file)


class EvidenceIncidentLogFormDataRepository(BaseRepository):
    model_class = EvidenceIncidentLogFormData
    pk_attr = "incident_log_id"

    def get(self, incident_log_id: UUID) -> EvidenceIncidentLogFormData | None:
        return super().get(incident_log_id)

    def delete(self, incident_log_form_data: EvidenceIncidentLogFormData) -> None:
        super().delete(incident_log_form_data)
