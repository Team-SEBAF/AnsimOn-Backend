from uuid import UUID

from app.base.base_repository import BaseRepository


class EvidenceRepositoryBase(BaseRepository):
    def list_by_complaint(self, complaint_id: UUID, limit: int):
        return (
            self.db.query(self.model_class)
            .filter(self.model_class.complaint_id == complaint_id)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
            .all()
        )

    def count_by_complaint(self, complaint_id: UUID) -> int:
        return (
            self.db.query(self.model_class)
            .filter(self.model_class.complaint_id == complaint_id)
            .count()
        )
