from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy.orm import Session


class EvidenceRepositoryBase:
    """Evidence 공통 레포. 서브클래스에서 model_class, pk_attr 지정."""

    model_class: ClassVar[type]
    pk_attr: ClassVar[str]  # "message_id", "voice_id" 등

    def __init__(self, db: Session):
        self.db = db

    def create(self, entity: Any) -> Any:
        self.db.add(entity)
        return entity

    def get(self, id: UUID) -> Any:
        return (
            self.db.query(self.model_class)
            .filter(getattr(self.model_class, self.pk_attr) == id)
            .one_or_none()
        )

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

    def delete(self, entity: Any) -> None:
        self.db.delete(entity)
