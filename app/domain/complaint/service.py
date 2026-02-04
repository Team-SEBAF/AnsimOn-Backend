from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthUser
from app.domain.complaint import schemas
from app.domain.complaint.repos.complaint_repository import ComplaintRepository


class ComplaintService:
    def get_my_complaint(
        self,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.ComplaintResponse:
        repo = ComplaintRepository(db)
        complaint = repo.get_by_user_sub(current_user.user_sub)

        if not complaint:
            raise HTTPException(status_code=404, detail="고소장을 찾을 수 없습니다.")

        return schemas.ComplaintResponse.model_validate(complaint)

    def update_my_complaint(
        self,
        request: schemas.UpdateComplaintRequest,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.ComplaintResponse:
        repo = ComplaintRepository(db)
        complaint = repo.get_by_user_sub(current_user.user_sub)

        if not complaint:
            raise HTTPException(status_code=404, detail="고소장을 찾을 수 없습니다.")

        repo.update(complaint, request.model_dump())
        db.commit()
        db.refresh(complaint)

        return schemas.ComplaintResponse.model_validate(complaint)


complaint_service = ComplaintService()
