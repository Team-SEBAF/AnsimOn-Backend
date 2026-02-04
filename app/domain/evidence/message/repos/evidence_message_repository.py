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

    def delete(self, message_id: UUID):
        message = self.get(message_id)
        if message:
            self.db.delete(message)
