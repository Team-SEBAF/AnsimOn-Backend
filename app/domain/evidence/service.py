from uuid import UUID

from sqlalchemy.orm import Session

from app.core.auth import AuthUser
from app.domain.evidence import schemas


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


evidence_service = EvidenceService()
