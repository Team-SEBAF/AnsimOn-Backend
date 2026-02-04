from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import schemas

from .repos.complaint_repository import ComplaintRepository

router = APIRouter(
    prefix="/api/v1/complaints",
    tags=["Complaint"],
)


@router.get(
    "/my-complaint",
    summary="고소장 정보 조회",
    description="고소장 정보를 조회합니다.",
    response_model=schemas.ComplaintResponse,
)
def get_complaint(
    current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    print(current_user.user_sub)
    complaint_repo = ComplaintRepository(db)
    complaint = complaint_repo.get_by_user_sub(current_user.user_sub)
    if not complaint:
        raise HTTPException(status_code=404, detail="고소장을 찾을 수 없습니다.")

    return schemas.ComplaintResponse.model_validate(complaint)
