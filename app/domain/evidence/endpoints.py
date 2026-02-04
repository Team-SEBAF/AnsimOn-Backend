from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.evidence import schemas
from app.domain.evidence.service import evidence_service

router = APIRouter(prefix="/api/v1/evidences", tags=["Evidence"])


@router.patch(
    "/{evidence_id}/filename",
    summary="증거 파일명 수정",
    description="증거 파일명을 수정합니다.",
    response_model=schemas.UpdateEvidenceFileNameResponse,
)
def update_evidence_filename(
    evidence_id: UUID,
    request: schemas.UpdateEvidenceFilenameRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return evidence_service.update_evidence_filename(
        evidence_id=evidence_id,
        request=request,
        current_user=current_user,
        db=db,
    )
