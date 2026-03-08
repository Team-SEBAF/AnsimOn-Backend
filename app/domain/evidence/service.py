from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser
from app.core.aws import delete_s3_objects, generate_presigned_put_url, get_s3_client
from app.core.database import SessionLocal
from app.core.settings import settings
from app.domain.complaint import Complaint, ComplaintRepository
from app.domain.evidence import schemas
from app.domain.evidence.constant import (
    EVIDENCE_DOCUMENT_RESTRICT,
    EVIDENCE_MESSAGE_RESTRICT,
    EVIDENCE_VICTIM_IMAGE_RESTRICT,
    EVIDENCE_VICTIM_RESTRICT,
    EVIDENCE_VICTIM_VIDEO_RESTRICT,
    EVIDENCE_VOICE_AUDIO_RESTRICT,
    EVIDENCE_VOICE_IMAGE_RESTRICT,
    EVIDENCE_VOICE_RESTRICT,
    EvidenceType,
    EvidenceTypeRestrict,
    MediaTypeRestrict,
)
from app.domain.evidence.errors.get_evidence_error import GetEvidenceErrorCode
from app.domain.evidence.errors.presigned_validation_error import (
    EvidencePresignedValidationErrorCode,
)


def _update_filename_dispatch(
    evidence_type: EvidenceType,
    evidence_id: UUID,
    filename: str,
    current_user: AuthUser,
    db: Session,
) -> tuple[UUID, str, Any]:
    if evidence_type == EvidenceType.MESSAGE:
        from app.domain.evidence_message.service import evidence_message_service

        entity = evidence_message_service.update_filename(
            message_id=evidence_id,
            filename=filename,
            current_user=current_user,
            db=db,
        )
        return entity.message_id, entity.filename, entity.updated_at
    elif evidence_type == EvidenceType.VOICE:
        from app.domain.evidence_voice.service import evidence_voice_service

        entity = evidence_voice_service.update_filename(
            voice_id=evidence_id,
            filename=filename,
            current_user=current_user,
            db=db,
        )
        return entity.voice_id, entity.filename, entity.updated_at
    elif evidence_type == EvidenceType.VICTIM:
        from app.domain.evidence_victim.service import evidence_victim_service

        entity = evidence_victim_service.update_filename(
            victim_id=evidence_id,
            filename=filename,
            current_user=current_user,
            db=db,
        )
        return entity.victim_id, entity.filename, entity.updated_at
    elif evidence_type == EvidenceType.REPORT_RECORD:
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
    elif evidence_type == EvidenceType.INCIDENT_LOG:
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
    evidence_type: EvidenceType,
    evidence_id: UUID,
    current_user: AuthUser,
    db: Session,
) -> None:
    if evidence_type == EvidenceType.MESSAGE:
        from app.domain.evidence_message.service import evidence_message_service

        evidence_message_service.delete_message(
            message_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return
    if evidence_type == EvidenceType.VOICE:
        from app.domain.evidence_voice.service import evidence_voice_service

        evidence_voice_service.delete_voice(
            voice_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return
    if evidence_type == EvidenceType.VICTIM:
        from app.domain.evidence_victim.service import evidence_victim_service

        evidence_victim_service.delete_victim(
            victim_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return
    if evidence_type == EvidenceType.REPORT_RECORD:
        from app.domain.evidence_report_record.service import (
            evidence_report_record_service,
        )

        evidence_report_record_service.delete_report_record(
            report_record_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return
    if evidence_type == EvidenceType.INCIDENT_LOG:
        from app.domain.evidence_incident_log.service import (
            evidence_incident_log_service,
        )

        evidence_incident_log_service.delete_incident_log_file(
            incident_log_id=evidence_id,
            current_user=current_user,
            db=db,
        )
        return


def _get_presigned_config(
    evidence_type: EvidenceType, complaint_id: UUID, db: Session
) -> tuple[EvidenceTypeRestrict, int, str]:
    restrict_map = {
        EvidenceType.MESSAGE: EVIDENCE_MESSAGE_RESTRICT,
        EvidenceType.VOICE: EVIDENCE_VOICE_RESTRICT,
        EvidenceType.VICTIM: EVIDENCE_VICTIM_RESTRICT,
        EvidenceType.REPORT_RECORD: EVIDENCE_DOCUMENT_RESTRICT,
        EvidenceType.INCIDENT_LOG: EVIDENCE_DOCUMENT_RESTRICT,
    }
    path_map = {
        EvidenceType.MESSAGE: "messages",
        EvidenceType.VOICE: "voices",
        EvidenceType.VICTIM: "victims",
        EvidenceType.REPORT_RECORD: "report-records",
        EvidenceType.INCIDENT_LOG: "incident-logs",
    }
    if evidence_type == EvidenceType.MESSAGE:
        from app.domain.evidence_message.repos.evidence_message_repository import (
            EvidenceMessageRepository,
        )

        total_count = EvidenceMessageRepository(db).count_by_complaint(complaint_id)
    elif evidence_type == EvidenceType.VOICE:
        from app.domain.evidence_voice.repos.evidence_voice_repository import (
            EvidenceVoiceRepository,
        )

        total_count = EvidenceVoiceRepository(db).count_by_complaint(complaint_id)
    elif evidence_type == EvidenceType.VICTIM:
        from app.domain.evidence_victim.repos.evidence_victim_repository import (
            EvidenceVictimRepository,
        )

        total_count = EvidenceVictimRepository(db).count_by_complaint(complaint_id)
    elif evidence_type == EvidenceType.REPORT_RECORD:
        from app.domain.evidence_report_record.repos.evidence_report_record_repository import (
            EvidenceReportRecordRepository,
        )

        total_count = EvidenceReportRecordRepository(db).count_by_complaint(complaint_id)
    elif evidence_type == EvidenceType.INCIDENT_LOG:
        from app.domain.evidence_incident_log.repos.evidence_incident_log_repository import (
            EvidenceIncidentLogRepository,
        )

        total_count = EvidenceIncidentLogRepository(db).count_by_complaint(complaint_id)

    return restrict_map[evidence_type], total_count, path_map[evidence_type]


def _get_item_restrict(
    evidence_type: EvidenceType,
    content_type: str,
    type_restrict: EvidenceTypeRestrict,
) -> EvidenceTypeRestrict | MediaTypeRestrict | None:
    """item별 적용할 restrict. VICTIM/VOICE는 content_type에 따라 VIDEO/AUDIO/IMAGE 등 선택."""
    if evidence_type == EvidenceType.VICTIM:
        if content_type in EVIDENCE_VICTIM_VIDEO_RESTRICT.allowed_types:
            return EVIDENCE_VICTIM_VIDEO_RESTRICT
        if content_type in EVIDENCE_VICTIM_IMAGE_RESTRICT.allowed_types:
            return EVIDENCE_VICTIM_IMAGE_RESTRICT
        return None
    if evidence_type == EvidenceType.VOICE:
        if content_type in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types:
            return EVIDENCE_VOICE_AUDIO_RESTRICT
        if content_type in EVIDENCE_VOICE_IMAGE_RESTRICT.allowed_types:
            return EVIDENCE_VOICE_IMAGE_RESTRICT
        return None
    return type_restrict


class EvidenceService:
    def get_presigned_url(
        self,
        complaint: Complaint,
        request: schemas.EvidencePresignedUrlRequest,
        db: Session,
    ) -> schemas.EvidencePresignedUrlResponse:
        restrict, total_count, path_segment = _get_presigned_config(
            request.type, complaint.complaint_id, db
        )

        is_total_count_valid = total_count + len(request.items) <= restrict.max_count
        content_type_failed_index_list: list[int] = []
        size_bytes_failed_index_list: list[int] = []
        duration_seconds_failed_index_list: list[int] = []

        for item in request.items:
            r = _get_item_restrict(request.type, item.content_type, restrict)
            if r is None or item.content_type not in r.allowed_types:
                content_type_failed_index_list.append(item.index)
                continue
            if item.size_bytes > r.max_size_bytes:
                size_bytes_failed_index_list.append(item.index)
            if r.max_duration_seconds is not None and (
                item.duration_seconds is None or item.duration_seconds > r.max_duration_seconds
            ):
                duration_seconds_failed_index_list.append(item.index)

        has_failures = (
            not is_total_count_valid
            or content_type_failed_index_list
            or size_bytes_failed_index_list
            or duration_seconds_failed_index_list
        )
        if has_failures:
            detail: dict = {
                "is_total_count_valid": is_total_count_valid,
                "content_type_failed_index_list": content_type_failed_index_list,
                "size_bytes_failed_index_list": size_bytes_failed_index_list,
            }
            if duration_seconds_failed_index_list:
                detail["duration_seconds_failed_index_list"] = duration_seconds_failed_index_list
            raise CodeException(
                code=EvidencePresignedValidationErrorCode.EVIDENCE_PRESIGNED_VALIDATION_FAILED,
                message="증거 유효성 검사에 통과하지 못한 증거가 존재하여 작업이 중단되었습니다.",
                debug_message="증거 유효성 검사에 통과하지 못한 증거가 존재하여 presigned URL 발급이 중단되었습니다. failed_index_list를 확인해주세요.",
                status_code=400,
                detail=detail,
            )

        items: list[schemas.EvidencePresignedUrlItemResponse] = []
        for item in request.items:
            evidence_id = uuid4()
            s3_key = (
                f"{complaint.user_sub}/complaints/"
                f"{complaint.complaint_id}/evidences/{path_segment}/{evidence_id}/original"
            )
            url = generate_presigned_put_url(
                bucket=settings.S3_BUCKET_NAME,
                key=s3_key,
                content_type=item.content_type,
                expires_in=600,  # 10분
            )
            items.append(
                schemas.EvidencePresignedUrlItemResponse(
                    index=item.index,
                    filename=item.filename,
                    url=url,
                    evidence_id=evidence_id,
                )
            )

        return schemas.EvidencePresignedUrlResponse(items=items)

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
            evidence_id=id_val,
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
                message="증거를 찾을 수 없습니다.",
                debug_message=f"evidence_id: {evidence_id}에 해당하는 증거를 찾을 수 없습니다.",
                status_code=404,
            )
        return evidence

    def _get_presigned_url(self, *, s3_key: str, expires_in: int):
        s3 = get_s3_client()

        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": s3_key,
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
                message="해당 증거에 대한 접근 권한이 없습니다.",
                debug_message=f"evidence_id: {evidence_id}에 해당하는 증거 접근 권한이 없습니다.",
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

    def get_original(
        self,
        type: EvidenceType,
        evidence_id: UUID,
        current_user: AuthUser,
        db: Session,
        repo: Any,
    ) -> Any:
        entity = self._get_evidence_and_check_access(evidence_id, repo, current_user, db)
        url = self._get_presigned_url(s3_key=entity.s3_key, expires_in=60 * 10)
        return schemas.EvidenceOriginalResponse(
            evidence_id=getattr(entity, repo.pk_attr),
            filename=entity.filename,
            content_type=entity.content_type,
            size_bytes=entity.size_bytes,
            url=url,
        )

    def update_evidence_filename(
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

    def delete_evidence_with_s3(
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
                debug_message=f"evidence_id: {evidence_id}에 해당하는 증거 삭제에 실패했습니다.",
                status_code=500,
            )
        repo.delete(entity)
        db.commit()


evidence_service = EvidenceService()
evidence_type_service = EvidenceTypeService()
