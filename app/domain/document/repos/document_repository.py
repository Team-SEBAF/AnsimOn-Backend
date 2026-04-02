from uuid import UUID

from app.base.base_repository import BaseRepository
from app.domain.document.models import Document


class DocumentRepository(BaseRepository):
    model_class = Document
    pk_attr = "id"

    def get_by_complaint_id(self, complaint_id: UUID) -> Document | None:
        return self.db.query(Document).filter(Document.complaint_id == complaint_id).first()
