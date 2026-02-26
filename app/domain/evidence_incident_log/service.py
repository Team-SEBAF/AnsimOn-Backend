from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser
from app.core.aws import delete_s3_objects
from app.core.settings import settings  # 1시간
from app.domain.complaint import Complaint
from app.domain.evidence import EvidenceTypeService
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.errors.register_validation_error import (
    raise_evidence_register_validation_failed,
)
from app.domain.evidence.utils import (
    check_register_max_count,
    fetch_s3_metadata_for_register,
)
from app.domain.evidence_incident_log import schemas
from app.domain.evidence_incident_log.errors.incident_log_type_mismatch_error import (
    IncidentLogTypeMismatchErrorCode,
)
from app.domain.evidence_incident_log.models.evidence_incident_log_model import (
    EvidenceIncidentLog,
    EvidenceIncidentLogFile,
    EvidenceIncidentLogFormData,
    EvidenceIncidentLogType,
)
from app.domain.evidence_incident_log.repos.evidence_incident_log_repository import (
    EvidenceIncidentLogFileRepository,
    EvidenceIncidentLogFormDataRepository,
    EvidenceIncidentLogRepository,
)


def _validate_incident_log_register_restrict(metadata_list: list[dict]) -> None:
    """content_type 먼저, 통과한 것만 size. duration 없음."""
    restrict = EVIDENCE_DOCUMENT_RESTRICT
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
        if total_count >= EVIDENCE_DOCUMENT_RESTRICT.max_count:
            raise CodeException(
                code=EvidenceMaxCountExceededErrorCode.EVIDENCE_MAX_COUNT_EXCEEDED,
                message="해당 증거 타입의 최대 개수를 초과했습니다.",
                debug_message=f"INCIDENT_LOG 타입 사건 일지 파일의 최대 개수({EVIDENCE_DOCUMENT_RESTRICT.max_count}개)를 초과했습니다.",
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
            restrict=EVIDENCE_DOCUMENT_RESTRICT,
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
            }
            for m in metadata_list
        ]

        db.bulk_insert_mappings(EvidenceIncidentLog, incident_log_rows)
        db.bulk_insert_mappings(EvidenceIncidentLogFile, incident_log_file_rows)
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
            witness=request.witness,
            perceived_risk=request.perceived_risk,
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
            witness=incident_log_form_data.witness,
            perceived_risk=incident_log_form_data.perceived_risk,
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
            witness=form_data_row.witness,
            perceived_risk=form_data_row.perceived_risk,
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

        form_data_fields = {"date", "time", "location", "description", "witness", "perceived_risk"}
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
            witness=form_data_row.witness,
            perceived_risk=form_data_row.perceived_risk,
            created_at=log.created_at,
            updated_at=log.updated_at,
        )

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
            delete_s3_objects(settings.S3_BUCKET_NAME, [file_row.s3_key])
            file_repo.delete(file_row)

        elif log.type == EvidenceIncidentLogType.FORM_DATA:
            form_data_repo = EvidenceIncidentLogFormDataRepository(db)
            form_data_row = form_data_repo.get(incident_log_id)
            form_data_repo.delete(form_data_row)

        incident_log_repo.delete(log)
        db.commit()


evidence_incident_log_service = EvidenceIncidentLogService()
