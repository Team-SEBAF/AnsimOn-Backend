from uuid import UUID

from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser
from app.core.aws import get_s3_client
from app.core.settings import settings
from app.domain.complaint import ComplaintRepository
from app.domain.evidence import schemas
from app.domain.evidence.errors.get_evidence_error import GetEvidenceErrorCode


class EvidenceService:
    def update_evidence_filename(
        self,
        evidence_id: UUID,
        request: schemas.UpdateEvidenceFilenameRequest,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.UpdateEvidenceFileNameResponse:
        if request.type == schemas.EvidenceType.MESSAGE:
            from app.domain.evidence_message.service import evidence_message_service

            message = evidence_message_service.update_filename(
                message_id=evidence_id,
                filename=request.filename,
                current_user=current_user,
                db=db,
            )
            return schemas.UpdateEvidenceFileNameResponse(
                id=message.message_id,
                filename=message.filename,
                updated_at=message.updated_at,
            )
        else:
            raise NotImplementedError(f"증거 타입 {request.type.value} 파일명 수정은 미구현입니다.")

    def delete_evidence(
        self,
        evidence_id: UUID,
        request: schemas.DeleteEvidenceRequest,
        current_user: AuthUser,
        db: Session,
    ) -> None:
        if request.type == schemas.EvidenceType.MESSAGE:
            from app.domain.evidence_message.service import evidence_message_service

            evidence_message_service.delete_message(
                message_id=evidence_id,
                current_user=current_user,
                db=db,
            )
        else:
            raise NotImplementedError(f"증거 타입 {request.type.value} 삭제는 미구현입니다.")


class EvidenceTypeService:
    def _get_evidence(self, evidence_id: UUID, repo: any):
        evidence = repo.get(evidence_id)
        if not evidence:
            raise CodeException(
                code=GetEvidenceErrorCode.EVIDENCE_NOT_FOUND,
                message=f"evidence_id: {evidence_id}에 해당하는 증거를 찾을 수 없습니다.",
                status_code=404,
            )
        return evidence

    def _get_presigned_url(self, *, evidence: any, variant: any, expires_in: int):
        s3 = get_s3_client()

        base = evidence.s3_key.rsplit("/", 1)[0]
        key = f"{base}/{variant.value}"

        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": key,
            },
            ExpiresIn=expires_in,
        )
        return url

    def _check_access_permission(
        self, *, complaint_id: UUID, evidence_id: UUID, current_user: AuthUser, db: Session
    ):
        complaint_repo = ComplaintRepository(db)
        complaint = complaint_repo.get(complaint_id)
        if complaint.user_sub != current_user.user_sub:
            raise CodeException(
                code=GetEvidenceErrorCode.NO_PERMISSION,
                message=f"evidence_id: {evidence_id}에 해당하는 증거 접근 권한이 없습니다.",
                status_code=403,
            )


evidence_service = EvidenceService()
evidence_type_service = EvidenceTypeService()
