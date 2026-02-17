from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import app.domain.evidence.errors.presigned_validation_error as presigned_validation_errors
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence import schemas
from app.domain.evidence.service import evidence_service

router = APIRouter(prefix="/api/v1/evidences", tags=["Evidence"])


@router.post(
    "/{complaint_id}/presigned-url",
    summary="증거 S3 업로드용 Presigned URL 발급 (복수 업로드 지원)",
    description="API Gateway 용량 제한이 10MB이기 때문에, 프론트엔드에서 Presigned URL로 S3에 직접 업로드 후 register API를 호출합니다.",
    response_model=schemas.EvidencePresignedUrlResponse,
    responses=presigned_validation_errors.EVIDENCE_PRESIGNED_VALIDATION_ERRORS_RESPONSES,
)
def get_evidence_presigned_url(
    complaint: Complaint = Depends(get_owned_complaint),
    request: schemas.EvidencePresignedUrlRequest = ...,
    db: Session = Depends(get_db),
):
    return evidence_service.get_presigned_url(
        complaint=complaint,
        request=request,
        db=db,
    )


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


@router.delete(
    "",
    summary="증거 삭제",
    description="같은 타입의 증거를 여러 건 삭제할 수 있습니다.",
    status_code=204,
)
def delete_evidence(
    request: schemas.DeleteEvidenceRequest,
    current_user: AuthUser = Depends(get_current_user),
):
    evidence_service.delete_evidence(
        request=request,
        current_user=current_user,
    )
