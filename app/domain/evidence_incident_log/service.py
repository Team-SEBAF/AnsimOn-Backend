from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser
from app.core.aws import delete_s3_objects, upload_fileobj
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence import EvidenceTypeService
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.utils import filter_evidence_files
from app.domain.evidence_incident_log import schemas
from app.domain.evidence_incident_log.models.evidence_incident_log_model import (
    EvidenceIncidentLog,
    EvidenceIncidentLogFile,
    EvidenceIncidentLogType,
)
from app.domain.evidence_incident_log.repos.evidence_incident_log_repository import (
    EvidenceIncidentLogFileRepository,
    EvidenceIncidentLogFormDataRepository,
    EvidenceIncidentLogRepository,
)


class EvidenceIncidentLogService(EvidenceTypeService):
    def _get_incident_log(
        self,
        incident_log_id: UUID,
        db: Session,
    ) -> EvidenceIncidentLog:
        evidence = super()._get_evidence(
            evidence_id=incident_log_id, repo=EvidenceIncidentLogRepository(db)
        )
        if evidence.type == EvidenceIncidentLogType.FILE:
            return super()._get_evidence(
                evidence_id=incident_log_id,
                repo=EvidenceIncidentLogFileRepository(db),
            )
        elif evidence.type == EvidenceIncidentLogType.FORM_DATA:
            return super()._get_evidence(
                evidence_id=incident_log_id,
                repo=EvidenceIncidentLogFormDataRepository(db),
            )

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

    def _check_access_permission(
        self, incident_log: EvidenceIncidentLog, current_user: AuthUser, db: Session
    ) -> None:
        return super()._check_access_permission(
            complaint_id=incident_log.complaint_id,
            evidence_id=incident_log.incident_log_id,
            current_user=current_user,
            db=db,
        )

    def upload_incident_log_files(
        self,
        complaint: Complaint,
        files: list[UploadFile],
        db: Session,
    ) -> schemas.EvidenceIncidentLogFileUploadResponse:
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        if total_count >= EVIDENCE_DOCUMENT_RESTRICT.max_count:
            raise CodeException(
                code=EvidenceMaxCountExceededErrorCode.EVIDENCE_MAX_COUNT_EXCEEDED,
                message=f"INCIDENT_LOG 타입 사건 일지 파일의 최대 개수({EVIDENCE_DOCUMENT_RESTRICT.max_count}개)를 초과했습니다.",
                status_code=400,
            )

        evidence_incident_log_repo = EvidenceIncidentLogRepository(db)
        evidence_incident_log_file_repo = EvidenceIncidentLogFileRepository(db)
        results: list[tuple[EvidenceIncidentLog, int]] = []

        # 신고・사건 일지 파일 필터링
        filtered_result = filter_evidence_files(files, EVIDENCE_DOCUMENT_RESTRICT)
        valid_files = filtered_result["valid_files"]

        # 최대 개수 초과 체크
        available_count = EVIDENCE_DOCUMENT_RESTRICT.max_count - total_count
        upload_files = valid_files[:available_count]

        count_invalid_files = valid_files[available_count:]
        count_invalid_filenames = [file.filename for file in count_invalid_files]

        with ThreadPoolExecutor(max_workers=3) as executor:
            for file in upload_files:
                # 파일 바이트 읽기 (1회)
                file_bytes = file.file.read()

                # incident_log_id 생성
                incident_log_id = uuid4()

                s3_key = (
                    f"{complaint.user_sub}/complaints/"
                    f"{complaint.complaint_id}/evidences/incident-logs/{incident_log_id}/original"
                )

                # S3 업로드 (병렬)
                futures = [
                    executor.submit(
                        upload_fileobj,
                        fileobj=BytesIO(file_bytes),
                        bucket=settings.S3_BUCKET_NAME,
                        key=s3_key,
                        content_type=file.content_type,
                    ),
                ]

                # 업로드 실패 시 예외 전파
                for future in futures:
                    future.result()

                # DB row 생성
                incident_log = EvidenceIncidentLog(
                    incident_log_id=incident_log_id,
                    complaint_id=complaint.complaint_id,
                    name=file.filename,
                    type=EvidenceIncidentLogType.FILE,
                )
                evidence_incident_log_repo.create(incident_log)

                size_bytes = len(file_bytes)
                incident_log_file = EvidenceIncidentLogFile(
                    incident_log_id=incident_log_id,
                    s3_key=s3_key,
                    content_type=file.content_type,
                    size_bytes=size_bytes,
                )
                evidence_incident_log_file_repo.create(incident_log_file)

                results.append((incident_log, size_bytes))

        db.commit()

        return schemas.EvidenceIncidentLogFileUploadResponse(
            incident_log_files=[
                schemas.EvidenceIncidentLogFileResponse(
                    incident_log_id=log.incident_log_id,
                    filename=log.name,
                    size_bytes=size_bytes,
                    created_at=log.created_at,
                    updated_at=log.updated_at,
                )
                for log, size_bytes in results
            ],
            type_invalid_filenames=filtered_result["type_invalid_filenames"],
            count_invalid_filenames=count_invalid_filenames,
            size_invalid_filenames=filtered_result["size_invalid_filenames"],
        )

    def update_filename(
        self,
        incident_log_id: UUID,
        filename: str,
        current_user: AuthUser,
        db: Session,
    ) -> EvidenceIncidentLog:
        return self._update_evidence_filename(
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
        file_repo = EvidenceIncidentLogFileRepository(db)

        log = super()._get_evidence(incident_log_id, incident_log_repo)
        EvidenceTypeService._check_access_permission(
            self,
            complaint_id=log.complaint_id,
            evidence_id=log.incident_log_id,
            current_user=current_user,
            db=db,
        )

        if log.type != EvidenceIncidentLogType.FILE:
            raise CodeException(
                code="INCIDENT_LOG_FORM_DATA_CANNOT_DELETE",
                message="사건 일지 폼 데이터는 해당 API를 사용해주세요.",
                status_code=400,
            )

        file_row = file_repo.get(incident_log_id)
        if file_row:
            try:
                delete_s3_objects(settings.S3_BUCKET_NAME, [file_row.s3_key])
            except Exception:
                raise CodeException(
                    code="DELETE_EVIDENCE_FAILED",
                    message="증거 삭제에 실패했습니다.",
                    status_code=500,
                )
            file_repo.delete(file_row)
        incident_log_repo.delete(log)
        db.commit()


evidence_incident_log_service = EvidenceIncidentLogService()
