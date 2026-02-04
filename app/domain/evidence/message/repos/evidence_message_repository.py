from uuid import UUID

from sqlalchemy.orm import Session

from ..models.evidence_message_model import EvidenceMessage


class EvidenceMessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, message: EvidenceMessage) -> EvidenceMessage:
        self.db.add(message)
        return message

    def get(self, message_id: UUID) -> EvidenceMessage | None:
        return (
            self.db.query(EvidenceMessage)
            .filter(EvidenceMessage.message_id == message_id)
            .one_or_none()
        )

    def list_by_complaint(self, complaint_id: UUID, limit: int):
        return (
            self.db.query(EvidenceMessage)
            .filter(EvidenceMessage.complaint_id == complaint_id)
            .order_by(EvidenceMessage.created_at.desc())
            .limit(limit)
            .all()
        )

    def count_by_complaint(self, complaint_id: UUID) -> int:
        return (
            self.db.query(EvidenceMessage)
            .filter(EvidenceMessage.complaint_id == complaint_id)
            .count()
        )

    def delete(self, message_id: UUID):
        message = self.get(message_id)
        if message:
            self.db.delete(message)
