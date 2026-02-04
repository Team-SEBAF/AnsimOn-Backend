from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint.errors.get_complaint_error import GetComplaintErrorCode

from .models.complaint_model import Complaint
from .repos.complaint_repository import ComplaintRepository


def get_owned_complaint(
    complaint_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Complaint:
    repo = ComplaintRepository(db)
    complaint = repo.get(complaint_id)

    if not complaint:
        raise CodeException(
            code=GetComplaintErrorCode.COMPLAINT_NOT_FOUND,
            message="고소장을 찾을 수 없습니다.",
            status_code=404,
        )

    if complaint.user_sub != current_user.user_sub:
        raise CodeException(
            code=GetComplaintErrorCode.NO_PERMISSION,
            message="고소장 접근 권한이 없습니다.",
            status_code=403,
        )

    return complaint
