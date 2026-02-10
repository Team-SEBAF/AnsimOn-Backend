from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser
from app.core.aws import delete_s3_objects, get_s3_client
from app.core.database import SessionLocal
from app.core.settings import settings
from app.domain.complaint import ComplaintRepository
from app.domain.evidence import schemas
from app.domain.evidence.errors.get_evidence_error import GetEvidenceErrorCode


def _update_filename_dispatch(
    evidence_type: schemas.EvidenceType,
    evidence_id: UUID,
    filename: str,
    current_user: AuthUser,
    db: Session,
) -> tuple[UUID, str, Any]:
    if evidence_type == schemas.EvidenceType.MESSAGE:
        from app.domain.evidence_message.service import evidence_message_service

        entity = evidence_message_service.update_filename(
            message_id=evidence_id,
            filename=filename,
            current_user=current_user,
            db=db,
        )
        return entity.message_id, entity.filename, entity.updated_at
    elif evidence_type == schemas.EvidenceType.VOICE:
        from app.domain.evidence_voice.service import evidence_voice_service

        entity = evidence_voice_service.update_filename(
            voice_id=evidence_id,
            filename=filename,
            current_user=current_user,
            db=db,
        )
        return entity.voice_id, entity.filename, entity.updated_at
    elif evidence_type == schemas.EvidenceType.TRACKING:
        from app.domain.evidence_tracking.service import evidence_tracking_service

        entity = evidence_tracking_service.update_filename(
            tracking_id=evidence_id,
            filename=filename,
            current_user=current_user,
            db=db,
        )
        return entity.tracking_id, entity.filename, entity.updated_at
    elif evidence_type == schemas.EvidenceType.REPORT_RECORD:
        from app.domain.evidence_report_record.service import (
            evidence_report_record_service,
        )

        entity = evidence_report_record_service.update_filename(
            report_record_id=evidence_id,
            filename=filename,
            current_user=current_user,
            db=db,
        )
        return entity.report_record_id, entity.filename, entity.updated_at
    elif evidence_type == schemas.EvidenceType.INCIDENT_LOG:
        from app.domain.evidence_incident_log.service import (
            evidence_incident_log_service,
        )

        entity = evidence_incident_log_service.update_filename(
            incident_log_id=evidence_id,
            filename=filename,
            current_user=current_user,
            db=db,
        )
        return entity.incident_log_id, entity.name, entity.updated_at


def _delete_evidence_dispatch(
    evidence_type: schemas.EvidenceType,
    evidence_id: UUID,
    current_user: AuthUser,
    db: Session,
) -> None:
    if evidence_type == schemas.EvidenceType.MESSAGE:
        from app.domain.evidence_message.service import evidence_message_service

        evidence_message_service.delete_message(
            message_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return
    if evidence_type == schemas.EvidenceType.VOICE:
        from app.domain.evidence_voice.service import evidence_voice_service

        evidence_voice_service.delete_voice(
            voice_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return
    if evidence_type == schemas.EvidenceType.TRACKING:
        from app.domain.evidence_tracking.service import evidence_tracking_service

        evidence_tracking_service.delete_tracking(
            tracking_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return
    if evidence_type == schemas.EvidenceType.REPORT_RECORD:
        from app.domain.evidence_report_record.service import (
            evidence_report_record_service,
        )

        evidence_report_record_service.delete_report_record(
            report_record_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return
    if evidence_type == schemas.EvidenceType.INCIDENT_LOG:
        from app.domain.evidence_incident_log.service import (
            evidence_incident_log_service,
        )

        evidence_incident_log_service.delete_incident_log_file(
            incident_log_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return


class EvidenceService:
    def update_evidence_filename(
        self,
        evidence_id: UUID,
        request: schemas.UpdateEvidenceFilenameRequest,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.UpdateEvidenceFileNameResponse:
        id_val, filename_val, updated_at = _update_filename_dispatch(
            request.type,
            evidence_id,
            request.filename,
            current_user,
            db,
        )
        return schemas.UpdateEvidenceFileNameResponse(
            id=id_val,
            filename=filename_val,
            updated_at=updated_at,
        )

    def delete_evidence(
        self,
        request: schemas.DeleteEvidenceRequest,
        current_user: AuthUser,
    ) -> None:
        def _delete_one(evidence_id: UUID) -> None:
            session = SessionLocal()
            try:
                _delete_evidence_dispatch(
                    request.type,
                    evidence_id,
                    current_user,
                    session,
                )
            finally:
                session.close()

        max_workers = min(len(request.evidence_ids), 4)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_delete_one, eid) for eid in request.evidence_ids]
            for future in futures:
                future.result()


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

    def _get_evidence_and_check_access(
        self,
        evidence_id: UUID,
        repo: Any,
        current_user: AuthUser,
        db: Session,
    ) -> Any:
        entity = self._get_evidence(evidence_id, repo)
        # 서브클래스가 (entity, ...) 시그니처로 오버라이드하므로, 베이스 시그니처는 명시 호출
        EvidenceTypeService._check_access_permission(
            self,
            complaint_id=entity.complaint_id,
            evidence_id=getattr(entity, repo.pk_attr),
            current_user=current_user,
            db=db,
        )
        return entity

    def _update_evidence_filename(
        self,
        evidence_id: UUID,
        filename: str,
        current_user: AuthUser,
        db: Session,
        repo: Any,
        *,
        filename_attr: str = "filename",
    ) -> Any:
        entity = self._get_evidence_and_check_access(evidence_id, repo, current_user, db)
        setattr(entity, filename_attr, filename)
        db.commit()
        db.refresh(entity)
        return entity

    def _delete_evidence_with_s3(
        self,
        evidence_id: UUID,
        current_user: AuthUser,
        db: Session,
        repo: Any,
        s3_keys_fn: Any,
    ) -> None:
        entity = self._get_evidence_and_check_access(evidence_id, repo, current_user, db)
        s3_keys = s3_keys_fn(entity)
        try:
            delete_s3_objects(settings.S3_BUCKET_NAME, s3_keys)
        except Exception:
            raise CodeException(
                code="DELETE_EVIDENCE_FAILED",
                message="증거 삭제에 실패했습니다.",
                status_code=500,
            )
        repo.delete(entity)
        db.commit()


evidence_service = EvidenceService()
evidence_type_service = EvidenceTypeService()
