from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint, schemas
from app.domain.complaint.service import complaint_service

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
def get_complaint(complaint: Complaint = Depends(get_owned_complaint)):
    return schemas.ComplaintResponse.model_validate(complaint)


@router.patch(
    "/my-complaint",
    summary="고소장 정보 수정",
    description="고소장 정보를 수정합니다.",
    response_model=schemas.ComplaintResponse,
)
def update_complaint(
    request: schemas.UpdateComplaintRequest,
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    return complaint_service.update_my_complaint(request, complaint, db)
