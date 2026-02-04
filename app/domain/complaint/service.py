from sqlalchemy.orm import Session

from app.domain.complaint import Complaint, schemas
from app.domain.complaint.repos.complaint_repository import ComplaintRepository


class ComplaintService:
    def update_my_complaint(
        self,
        request: schemas.UpdateComplaintRequest,
        complaint: Complaint,
        db: Session,
    ) -> schemas.ComplaintResponse:
        repo = ComplaintRepository(db)
        repo.update(complaint, request.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(complaint)

        return schemas.ComplaintResponse.model_validate(complaint)


complaint_service = ComplaintService()
