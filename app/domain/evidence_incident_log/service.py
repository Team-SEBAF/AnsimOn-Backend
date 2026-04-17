from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import BytesIO
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser
from app.core.aws import delete_s3_by_prefixes, download_s3_object, head_s3_object, upload_fileobj
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence import EvidenceTypeService
from app.domain.evidence.constant import (
    EVIDENCE_IMAGE_RESTRICT,
    EVIDENCE_INCIDENT_LOG_RESTRICT,
    EVIDENCE_VIDEO_RESTRICT,
    EVIDENCE_VOICE_AUDIO_RESTRICT,
)
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.errors.register_validation_error import (
    raise_evidence_register_validation_failed,
)
from app.domain.evidence.utils import (
    check_register_max_count,
    collect_register_failures_from_metadata,
    fetch_s3_metadata_for_register,
    generate_presigned_urls_for_unrestricted_content,
    get_restrict_by_content_type,
)
from app.domain.evidence_incident_log import schemas
from app.domain.evidence_incident_log.constant import get_attachment_type_from_content_type
from app.domain.evidence_incident_log.errors.incident_log_type_mismatch_error import (
    IncidentLogTypeMismatchErrorCode,
)
from app.domain.evidence_incident_log.models.evidence_incident_log_model import (
    EvidenceIncidentLog,
    EvidenceIncidentLogFile,
    EvidenceIncidentLogFormData,
    EvidenceIncidentLogType,
)
from app.domain.evidence_incident_log.models.incident_log_form_data_attachment_model import (
    IncidentLogFormDataAttachment,
)
from app.domain.evidence_incident_log.repos.evidence_incident_log_repository import (
    EvidenceIncidentLogFileRepository,
    EvidenceIncidentLogFormDataRepository,
    EvidenceIncidentLogRepository,
)
from app.domain.evidence_incident_log.repos.incident_log_form_data_attachment_repository import (
    IncidentLogFormDataAttachmentRepository,
)
from app.domain.evidence_victim.utils import get_video_duration
from app.domain.evidence_voice.utils import get_audio_duration
from app.domain.timeline.repos.timeline_repository import TimelineRepository


def _validate_incident_log_register_restrict(metadata_list: list[dict]) -> None:
    """content_type 먼저, 통과한 것만 size. duration 없음."""
    restrict = EVIDENCE_INCIDENT_LOG_RESTRICT
    content_type_failed_evidence_ids: list[str] = []
    size_bytes_failed_evidence_ids: list[str] = []

    for m in metadata_list:
        eid_str = str(m["incident_log_id"])
        if m.get("content_type") not in restrict.allowed_types:
            content_type_failed_evidence_ids.append(eid_str)
            continue
        if m.get("size_bytes", 0) > restrict.max_size_bytes:
            size_bytes_failed_evidence_ids.append(eid_str)

    raise_evidence_register_validation_failed(
        content_type_failed_evidence_ids=content_type_failed_evidence_ids,
        size_bytes_failed_evidence_ids=size_bytes_failed_evidence_ids,
        duration_seconds_failed_evidence_ids=None,
    )


def _raise_form_data_attachment_register_validation_if_failed(
    size_bytes_failed_attachment_ids: list[str],
    duration_seconds_failed_attachment_ids: list[str],
    extraction_failed_attachment_ids: list[str],
) -> None:
    """2차: 전체 실패 수집 후 한 번에 raise."""
    duration_total = duration_seconds_failed_attachment_ids + extraction_failed_attachment_ids
    if not (size_bytes_failed_attachment_ids or duration_total):
        return
    raise_evidence_register_validation_failed(
        content_type_failed_evidence_ids=[],
        size_bytes_failed_evidence_ids=size_bytes_failed_attachment_ids,
        duration_seconds_failed_evidence_ids=duration_total if duration_total else [],
    )


class EvidenceIncidentLogService(EvidenceTypeService):
    def _get_incident_log_with_type_check(
        self,
        incident_log_id: UUID,
        type: EvidenceIncidentLogType,
        current_user: AuthUser,
        db: Session,
    ):
        incident_log_repo = EvidenceIncidentLogRepository(db)
        file_repo = EvidenceIncidentLogFileRepository(db)
        form_data_repo = EvidenceIncidentLogFormDataRepository(db)

        log = super()._get_evidence(incident_log_id, incident_log_repo)
        self._check_access_permission(
            incident_log=log,
            current_user=current_user,
            db=db,
        )

        if log.type != type:
            raise CodeException(
                code=IncidentLogTypeMismatchErrorCode.INCIDENT_LOG_TYPE_MISMATCH,
                message="사건 일지 타입이 불일치한 작업을 시도했습니다.",
                debug_message=f"ID: {incident_log_id}에 해당하는 사건 일지 타입이 {type.value}가 아닙니다.",
                status_code=400,
            )

        if type == EvidenceIncidentLogType.FILE:
            file_row = file_repo.get(incident_log_id)
            return log, file_row
        elif type == EvidenceIncidentLogType.FORM_DATA:
            form_data_row = form_data_repo.get(incident_log_id)
            return log, form_data_row

    def _get_attachments(self, incident_log_id: UUID, db: Session) -> list:
        attachment_repo = IncidentLogFormDataAttachmentRepository(db)
        attachments = attachment_repo.list_by_incident_log_id(incident_log_id)
        return [
            schemas.FormDataAttachmentResponse(
                attachment_id=att.attachment_id,
                type=get_attachment_type_from_content_type(att.content_type),
                filename=att.filename,
                content_type=att.content_type,
                size_bytes=att.size_bytes,
                duration_seconds=att.duration_seconds,
                created_at=att.created_at,
            )
            for att in attachments
        ]

    def _get_total_count(self, complaint_id: UUID, db: Session) -> int:
        repo = EvidenceIncidentLogRepository(db)
        return repo.count_by_complaint(complaint_id=complaint_id)

    def _get_limit_incident_logs_and_total_count(
        self,
        *,
        complaint: Complaint,
        limit: int,
        db: Session,
    ):
        repo = EvidenceIncidentLogRepository(db)

        # 최신순 조회
        incident_logs = repo.list_by_complaint(
            complaint_id=complaint.complaint_id,
            limit=limit,
        )

        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )

        return incident_logs, total_count

    def _get_file_rows(
        self, incident_logs: list[EvidenceIncidentLog], db: Session
    ) -> list[EvidenceIncidentLogFile]:
        file_repo = EvidenceIncidentLogFileRepository(db)
        file_log_ids = [
            log.incident_log_id for log in incident_logs if log.type == EvidenceIncidentLogType.FILE
        ]
        return file_repo.list_by_incident_log_ids(file_log_ids)

    def _check_access_permission(
        self, incident_log: EvidenceIncidentLog, current_user: AuthUser, db: Session
    ) -> None:
        return super()._check_access_permission(
            complaint_id=incident_log.complaint_id,
            evidence_id=incident_log.incident_log_id,
            current_user=current_user,
            db=db,
        )

    def _check_max_count(self, complaint_id: UUID, db: Session) -> None:
        total_count = self._get_total_count(
            complaint_id=complaint_id,
            db=db,
        )
        if total_count >= EVIDENCE_INCIDENT_LOG_RESTRICT.max_count:
            raise CodeException(
                code=EvidenceMaxCountExceededErrorCode.EVIDENCE_MAX_COUNT_EXCEEDED,
                message="해당 증거 타입의 최대 개수를 초과했습니다.",
                debug_message=f"INCIDENT_LOG 타입 사건 일지 파일의 최대 개수({EVIDENCE_INCIDENT_LOG_RESTRICT.max_count}개)를 초과했습니다.",
                status_code=400,
            )
        return total_count

    def register_incident_log_file(
        self,
        complaint: Complaint,
        request: schemas.EvidenceIncidentLogFileRegisterRequest,
        db: Session,
    ) -> schemas.EvidenceIncidentLogFileRegisterListResponse:
        # 1) max_count 검사
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        check_register_max_count(
            total_count=total_count,
            request_count=len(request.items),
            restrict=EVIDENCE_INCIDENT_LOG_RESTRICT,
            type_name="INCIDENT_LOG",
        )
        # 2) S3 메타데이터 조회
        metadata_list = fetch_s3_metadata_for_register(
            complaint=complaint,
            items=request.items,
            path_segment="incident-logs",
            get_evidence_id=lambda item: item.incident_log_id,
            build_extra=lambda item, s3_key, ct, size: {
                "incident_log_id": item.incident_log_id,
                "complaint_id": complaint.complaint_id,
                "filename": item.filename,
                "file_created_at": item.file_created_at,
            },
        )
        # 3) content_type, size 검증
        _validate_incident_log_register_restrict(metadata_list)
        # 4) DB 저장
        incident_log_rows = [
            {
                "incident_log_id": m["incident_log_id"],
                "complaint_id": m["complaint_id"],
                "name": m["filename"],
                "type": EvidenceIncidentLogType.FILE,
            }
            for m in metadata_list
        ]
        incident_log_file_rows = [
            {
                "incident_log_id": m["incident_log_id"],
                "s3_key": m["s3_key"],
                "content_type": m["content_type"],
                "size_bytes": m["size_bytes"],
                "file_created_at": m["file_created_at"],
            }
            for m in metadata_list
        ]

        db.bulk_insert_mappings(EvidenceIncidentLog, incident_log_rows)
        db.bulk_insert_mappings(EvidenceIncidentLogFile, incident_log_file_rows)
        TimelineRepository(db).set_regeneration_flags(
            complaint.complaint_id, need_timeline_regeneration=True
        )
        db.commit()

        results = [
            schemas.EvidenceIncidentLogFileRegisterItemResponse(
                incident_log_id=log_row["incident_log_id"],
                filename=log_row["name"],
                content_type=file_row["content_type"],
                size_bytes=file_row["size_bytes"],
            )
            for log_row, file_row in zip(incident_log_rows, incident_log_file_rows)
        ]
        return schemas.EvidenceIncidentLogFileRegisterListResponse(items=results)

    def get_preview_incident_logs(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceIncidentLogPreviewListResponse:
        incident_logs, total_count = self._get_limit_incident_logs_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        file_rows = self._get_file_rows(incident_logs, db)
        file_by_id = {row.incident_log_id: row for row in file_rows}

        previews = [
            schemas.EvidenceIncidentLogPreviewResponse(
                incident_log_id=incident_log.incident_log_id,
                type=incident_log.type,
                filename=incident_log.name,
                size_bytes=fr.size_bytes
                if (fr := file_by_id.get(incident_log.incident_log_id))
                else None,
            )
            for incident_log in incident_logs
        ]

        return schemas.EvidenceIncidentLogPreviewListResponse(
            previews=previews,
            total_count=total_count,
        )

    def get_detail_incident_logs(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceIncidentLogDetailListResponse:
        incident_logs, total_count = self._get_limit_incident_logs_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        file_rows = self._get_file_rows(incident_logs, db)
        file_by_id = {row.incident_log_id: row for row in file_rows}

        details = [
            schemas.EvidenceIncidentLogDetailResponse(
                incident_log_id=incident_log.incident_log_id,
                type=incident_log.type,
                filename=incident_log.name,
                size_bytes=fr.size_bytes
                if (fr := file_by_id.get(incident_log.incident_log_id))
                else None,
                content_type=fr.content_type if fr else None,
                created_at=incident_log.created_at,
                updated_at=incident_log.updated_at,
            )
            for incident_log in incident_logs
        ]
        return schemas.EvidenceIncidentLogDetailListResponse(
            details=details,
            total_count=total_count,
        )

    def get_original_incident_log_file(
        self,
        incident_log_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.EvidenceIncidentLogFileOriginalResponse:
        log, file_row = self._get_incident_log_with_type_check(
            incident_log_id, EvidenceIncidentLogType.FILE, current_user, db
        )

        url = super()._get_presigned_url(
            s3_key=file_row.s3_key,
            expires_in=60 * 10,  # 10분
        )

        return schemas.EvidenceIncidentLogFileOriginalResponse(
            incident_log_id=log.incident_log_id,
            filename=log.name,
            content_type=file_row.content_type,
            size_bytes=file_row.size_bytes,
            url=url,
            created_at=log.created_at,
            updated_at=log.updated_at,
        )

    def upload_incident_log_form_data(
        self,
        complaint: Complaint,
        request: schemas.EvidenceIncidentLogFormDataUploadRequest,
        db: Session,
    ) -> schemas.EvidenceIncidentLogFormDataResponse:
        self._check_max_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )

        incident_log_repo = EvidenceIncidentLogRepository(db)
        incident_log_form_data_repo = EvidenceIncidentLogFormDataRepository(db)
        incident_log_id = uuid4()

        incident_log = EvidenceIncidentLog(
            incident_log_id=incident_log_id,
            complaint_id=complaint.complaint_id,
            name=request.filename,
            type=EvidenceIncidentLogType.FORM_DATA,
        )
        incident_log_repo.create(incident_log)

        incident_log_form_data = EvidenceIncidentLogFormData(
            incident_log_id=incident_log_id,
            date=request.date,
            time=request.time,
            location=request.location,
            description=request.description,
        )
        incident_log_form_data_repo.create(incident_log_form_data)
        db.commit()

        db.refresh(incident_log)
        db.refresh(incident_log_form_data)

        return schemas.EvidenceIncidentLogFormDataResponse(
            incident_log_id=incident_log.incident_log_id,
            filename=incident_log.name,
            date=incident_log_form_data.date,
            time=incident_log_form_data.time,
            location=incident_log_form_data.location,
            description=incident_log_form_data.description,
            attachments=[],
            created_at=incident_log.created_at,
            updated_at=incident_log.updated_at,
        )

    def get_incident_log_form_data(
        self,
        incident_log_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.EvidenceIncidentLogFormDataResponse:
        log, form_data_row = self._get_incident_log_with_type_check(
            incident_log_id, EvidenceIncidentLogType.FORM_DATA, current_user, db
        )
        return schemas.EvidenceIncidentLogFormDataResponse(
            incident_log_id=log.incident_log_id,
            filename=log.name,
            date=form_data_row.date,
            time=form_data_row.time,
            location=form_data_row.location,
            description=form_data_row.description,
            attachments=self._get_attachments(incident_log_id, db),
            created_at=log.created_at,
            updated_at=log.updated_at,
        )

    def update_incident_log_form_data(
        self,
        incident_log_id: UUID,
        request: schemas.EvidenceIncidentLogFormDataUpdateRequest,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.EvidenceIncidentLogFormDataResponse:
        incident_log_repo = EvidenceIncidentLogRepository(db)
        log, form_data_row = self._get_incident_log_with_type_check(
            incident_log_id, EvidenceIncidentLogType.FORM_DATA, current_user, db
        )

        update_data = request.model_dump(exclude_unset=True)

        if "filename" in update_data:
            incident_log_repo.update(log, {"name": update_data["filename"]})

        form_data_fields = {"date", "time", "location", "description"}
        for key in form_data_fields:
            if key in update_data:
                setattr(form_data_row, key, update_data[key])

        db.commit()
        db.refresh(log)
        db.refresh(form_data_row)

        return schemas.EvidenceIncidentLogFormDataResponse(
            incident_log_id=incident_log_id,
            filename=log.name,
            date=form_data_row.date,
            time=form_data_row.time,
            location=form_data_row.location,
            description=form_data_row.description,
            attachments=self._get_attachments(incident_log_id, db),
            created_at=log.created_at,
            updated_at=log.updated_at,
        )

    def get_form_data_attachment_presigned_url(
        self,
        complaint: Complaint,
        incident_log_id: UUID,
        request: schemas.FormDataAttachmentPresignedRequest,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.FormDataAttachmentPresignedResponse:
        self._get_incident_log_with_type_check(
            incident_log_id, EvidenceIncidentLogType.FORM_DATA, current_user, db
        )
        path_segment = f"incident-logs/attachments/{incident_log_id}"

        def s3_key_builder(c: Complaint, eid: UUID) -> str:
            return (
                f"{c.user_sub}/complaints/{c.complaint_id}/evidences/{path_segment}/{eid}/original"
            )

        rows = generate_presigned_urls_for_unrestricted_content(
            complaint=complaint,
            items=request.items,
            s3_key_builder=s3_key_builder,
            id_field_name="attachment_id",
        )
        return schemas.FormDataAttachmentPresignedResponse(
            items=[
                schemas.FormDataAttachmentPresignedItemResponse(
                    index=r["index"],
                    filename=r["filename"],
                    url=r["url"],
                    attachment_id=r["attachment_id"],
                )
                for r in rows
            ]
        )

    def register_form_data_attachments(
        self,
        complaint: Complaint,
        incident_log_id: UUID,
        request: schemas.FormDataAttachmentRegisterRequest,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.FormDataAttachmentRegisterResponse:
        self._get_incident_log_with_type_check(
            incident_log_id, EvidenceIncidentLogType.FORM_DATA, current_user, db
        )
        path_segment = f"incident-logs/attachments/{incident_log_id}"
        metadata_list = fetch_s3_metadata_for_register(
            complaint=complaint,
            items=request.items,
            path_segment=path_segment,
            get_evidence_id=lambda item: item.attachment_id,
            build_extra=lambda item, s3_key, ct, size: {
                "attachment_id": item.attachment_id,
                "incident_log_id": incident_log_id,
                "filename": item.filename,
            },
        )
        (
            size_bytes_failed_ids,
            valid_metadata,
        ) = collect_register_failures_from_metadata(metadata_list, "attachment_id")

        def _process_attachment(m: dict) -> tuple[dict | None, str | None]:
            ct = m["content_type"]
            r = get_restrict_by_content_type(ct)
            duration_seconds = None
            if ct in EVIDENCE_VIDEO_RESTRICT.allowed_types:
                try:
                    file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
                    duration_seconds = get_video_duration(file_bytes)
                    if r.max_duration_seconds and duration_seconds > r.max_duration_seconds:
                        return None, str(m["attachment_id"])
                except Exception:
                    return None, str(m["attachment_id"])
            elif ct in EVIDENCE_IMAGE_RESTRICT.allowed_types:
                duration_seconds = 0
            elif ct in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types:
                try:
                    file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
                    duration_seconds = get_audio_duration(file_bytes)
                    if r.max_duration_seconds and duration_seconds > r.max_duration_seconds:
                        return None, str(m["attachment_id"])
                except (ValueError, TypeError):
                    return None, str(m["attachment_id"])
            row = {
                "attachment_id": m["attachment_id"],
                "incident_log_id": m["incident_log_id"],
                "filename": m["filename"],
                "s3_key": m["s3_key"],
                "content_type": ct,
                "size_bytes": m["size_bytes"],
                "duration_seconds": duration_seconds,
            }
            return row, None

        with ThreadPoolExecutor(max_workers=max(1, min(len(valid_metadata), 5))) as executor:
            results = list(executor.map(_process_attachment, valid_metadata))
        rows = [r for r, _ in results if r is not None]
        extraction_failed_attachment_ids = [eid for _, eid in results if eid is not None]
        duration_seconds_failed_attachment_ids: list[str] = []
        for r in rows:
            ct = r.get("content_type", "")
            restrict = get_restrict_by_content_type(ct)
            if restrict.max_duration_seconds is not None:
                dur = r.get("duration_seconds", 0)
                if dur > restrict.max_duration_seconds:
                    duration_seconds_failed_attachment_ids.append(str(r["attachment_id"]))
        _raise_form_data_attachment_register_validation_if_failed(
            size_bytes_failed_attachment_ids=size_bytes_failed_ids,
            duration_seconds_failed_attachment_ids=duration_seconds_failed_attachment_ids,
            extraction_failed_attachment_ids=extraction_failed_attachment_ids,
        )
        db.bulk_insert_mappings(IncidentLogFormDataAttachment, rows)
        db.commit()
        results_resp = [
            schemas.FormDataAttachmentRegisterItemResponse(
                attachment_id=r["attachment_id"],
                type=get_attachment_type_from_content_type(r["content_type"]),
                filename=r["filename"],
                content_type=r["content_type"],
                size_bytes=r["size_bytes"],
                duration_seconds=r["duration_seconds"],
            )
            for r in rows
        ]
        return schemas.FormDataAttachmentRegisterResponse(items=results_resp)

    def delete_form_data_attachments(
        self,
        incident_log_id: UUID,
        attachment_ids: list[UUID],
        current_user: AuthUser,
        db: Session,
    ) -> None:
        self._get_incident_log_with_type_check(
            incident_log_id, EvidenceIncidentLogType.FORM_DATA, current_user, db
        )
        attachment_repo = IncidentLogFormDataAttachmentRepository(db)
        attachments = attachment_repo.list_by_incident_log_id(incident_log_id)
        to_delete = [a for a in attachments if a.attachment_id in attachment_ids]
        if not to_delete:
            return
        prefixes = [a.s3_key.rsplit("/", 1)[0] + "/" for a in to_delete]
        delete_s3_by_prefixes(settings.S3_BUCKET_NAME, prefixes)
        for att in to_delete:
            attachment_repo.delete(att)
        db.commit()

    def delete_incident_log_file(
        self,
        incident_log_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> None:
        incident_log_repo = EvidenceIncidentLogRepository(db)
        log = super()._get_evidence(incident_log_id, incident_log_repo)

        self._check_access_permission(
            incident_log=log,
            current_user=current_user,
            db=db,
        )

        if log.type == EvidenceIncidentLogType.FILE:
            file_repo = EvidenceIncidentLogFileRepository(db)
            file_row = file_repo.get(incident_log_id)
            prefix = file_row.s3_key.rsplit("/", 1)[0] + "/"
            delete_s3_by_prefixes(settings.S3_BUCKET_NAME, [prefix])
            file_repo.delete(file_row)

        elif log.type == EvidenceIncidentLogType.FORM_DATA:
            attachment_repo = IncidentLogFormDataAttachmentRepository(db)
            attachments = attachment_repo.list_by_incident_log_id(incident_log_id)
            if attachments:
                prefix = attachments[0].s3_key.rsplit("/", 2)[0] + "/"
                delete_s3_by_prefixes(settings.S3_BUCKET_NAME, [prefix])
            form_data_repo = EvidenceIncidentLogFormDataRepository(db)
            form_data_row = form_data_repo.get(incident_log_id)
            form_data_repo.delete(form_data_row)

        incident_log_repo.delete(log)
        db.commit()

    def update_filename(
        self,
        incident_log_id: UUID,
        filename: str,
        current_user: AuthUser,
        db: Session,
    ) -> EvidenceIncidentLog:
        return self.update_evidence_filename(
            incident_log_id,
            filename,
            current_user,
            db,
            EvidenceIncidentLogRepository(db),
            filename_attr="name",
        )

    def ensure_form_data_pdf_and_get_s3_key(
        self,
        incident_log_id: UUID,
        complaint: Complaint,
        db: Session,
    ) -> tuple[str | None, list[str]]:
        """
        FORM_DATA 사건일지 PDF S3 키 반환. 없거나 재생성 필요 시 생성 후 저장.
        Returns: (main_pdf_s3_key, attachments_s3_keys)
        """
        incident_log_repo = EvidenceIncidentLogRepository(db)
        form_data_repo = EvidenceIncidentLogFormDataRepository(db)
        attachment_repo = IncidentLogFormDataAttachmentRepository(db)

        log = incident_log_repo.get(incident_log_id)
        form_data = form_data_repo.get(incident_log_id)

        default_s3_key = (
            f"{complaint.user_sub}/complaints/{complaint.complaint_id}/evidences/"
            f"incident-logs/{incident_log_id}/export-pdf"
        )
        s3_key = form_data.pdf_s3_key or default_s3_key

        need_regenerate = form_data.pdf_created_at is None or (
            form_data.updated_at > form_data.pdf_created_at
        )
        exists_in_s3 = head_s3_object(settings.S3_BUCKET_NAME, s3_key) is not None

        if need_regenerate or not exists_in_s3:
            from app.doc_generator.incident_log_form_data_pdf import (
                build_incident_log_from_data_pdf,
            )

            s3_key = default_s3_key
            date_str = form_data.date.strftime("%Y-%m-%d")
            time_str = form_data.time.strftime("%H:%M")
            pdf_bytes = build_incident_log_from_data_pdf(
                title=log.name,
                date_str=date_str,
                time_str=time_str,
                location=form_data.location,
                description=form_data.description,
            )
            upload_fileobj(
                fileobj=BytesIO(pdf_bytes),
                bucket=settings.S3_BUCKET_NAME,
                key=s3_key,
                content_type="application/pdf",
            )
            setattr(form_data, "pdf_created_at", datetime.now(timezone.utc))
            setattr(form_data, "pdf_s3_key", s3_key)
            db.commit()

        attachments = attachment_repo.list_by_incident_log_id(incident_log_id)
        attachment_s3_keys = [a.s3_key for a in attachments]

        return s3_key, attachment_s3_keys


evidence_incident_log_service = EvidenceIncidentLogService()
