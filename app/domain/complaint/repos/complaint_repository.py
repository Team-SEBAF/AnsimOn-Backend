from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.complaint.models.complaint_model import Complaint


class ComplaintRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, complaint: Complaint) -> Complaint:
        self.db.add(complaint)
        return complaint

    def get(self, complaint_id: UUID) -> Complaint | None:
        return self.db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()

    def update(
        self,
        complaint: Complaint,
        values: dict[str, object],
    ) -> Complaint:
        for key, value in values.items():
            if not hasattr(complaint, key):
                raise ValueError(f"Invalid field: {key}")
            setattr(complaint, key, value)
        return complaint
