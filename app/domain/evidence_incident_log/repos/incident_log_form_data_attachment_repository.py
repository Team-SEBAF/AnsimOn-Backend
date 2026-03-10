from uuid import UUID

from app.base.base_repository import BaseRepository

from ..models.incident_log_form_data_attachment_model import IncidentLogFormDataAttachment


class IncidentLogFormDataAttachmentRepository(BaseRepository):
    model_class = IncidentLogFormDataAttachment
    pk_attr = "attachment_id"

    def get(self, attachment_id: UUID) -> IncidentLogFormDataAttachment | None:
        return super().get(attachment_id)

    def list_by_incident_log_id(self, incident_log_id: UUID) -> list[IncidentLogFormDataAttachment]:
        return (
            self.db.query(self.model_class)
            .filter(self.model_class.incident_log_id == incident_log_id)
            .order_by(self.model_class.created_at)
            .all()
        )

    def count_by_incident_log_id(self, incident_log_id: UUID) -> int:
        return (
            self.db.query(self.model_class)
            .filter(self.model_class.incident_log_id == incident_log_id)
            .count()
        )
