from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser
from app.core.aws import upload_fileobj
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence import EvidenceTypeService
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.utils import filter_evidence_files
from app.domain.evidence_report_record import schemas
from app.domain.evidence_report_record.models.evidence_report_record_model import (
    EvidenceReportRecord,
)
from app.domain.evidence_report_record.repos.evidence_report_record_repository import (
    EvidenceReportRecordRepository,
)


class EvidenceReportRecordService(EvidenceTypeService):
    def _get_report_record(
        self,
        report_record_id: UUID,
        db: Session,
    ) -> EvidenceReportRecord:
        return super()._get_evidence(
            evidence_id=report_record_id, repo=EvidenceReportRecordRepository(db)
        )

    def _get_total_count(self, complaint_id: UUID, db: Session) -> int:
        repo = EvidenceReportRecordRepository(db)
        return repo.count_by_complaint(complaint_id=complaint_id)

    def _get_limit_report_records_and_total_count(
        self,
        *,
        complaint: Complaint,
        limit: int,
        db: Session,
    ):
        repo = EvidenceReportRecordRepository(db)

        # 최신순 조회
        report_records = repo.list_by_complaint(
            complaint_id=complaint.complaint_id,
            limit=limit,
        )

        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )

        return report_records, total_count

    def _check_access_permission(
        self, report_record: EvidenceReportRecord, current_user: AuthUser, db: Session
    ) -> None:
        return super()._check_access_permission(
            complaint_id=report_record.complaint_id,
            evidence_id=report_record.report_record_id,
            current_user=current_user,
            db=db,
        )

    def upload_report_records(
        self,
        complaint: Complaint,
        files: list[UploadFile],
        db: Session,
    ) -> schemas.EvidenceReportRecordUploadResponse:
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        if total_count >= EVIDENCE_DOCUMENT_RESTRICT.max_count:
            raise CodeException(
                code=EvidenceMaxCountExceededErrorCode.EVIDENCE_MAX_COUNT_EXCEEDED,
                message=f"REPORT_RECORD 타입 신고・사건 일지의 최대 개수({EVIDENCE_DOCUMENT_RESTRICT.max_count}개)를 초과했습니다.",
                status_code=400,
            )

        evidence_report_record_repo = EvidenceReportRecordRepository(db)
        results: list[EvidenceReportRecord] = []

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

                # report_record_id 생성
                report_record_id = uuid4()

                s3_key = (
                    f"{complaint.user_sub}/complaints/"
                    f"{complaint.complaint_id}/evidences/report-records/{report_record_id}/original"
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
                report_record = EvidenceReportRecord(
                    report_record_id=report_record_id,
                    complaint_id=complaint.complaint_id,
                    filename=file.filename,
                    s3_key=s3_key,
                    content_type=file.content_type,
                    size_bytes=len(file_bytes),
                )

                evidence_report_record_repo.create(report_record)
                results.append(report_record)

        db.commit()

        return schemas.EvidenceReportRecordUploadResponse(
            report_records=[
                schemas.EvidenceReportRecordResponse(
                    report_record_id=v.report_record_id,
                    filename=v.filename,
                    size_bytes=v.size_bytes,
                    created_at=v.created_at,
                    updated_at=v.updated_at,
                )
                for v in results
            ],
            type_invalid_filenames=filtered_result["type_invalid_filenames"],
            count_invalid_filenames=count_invalid_filenames,
            size_invalid_filenames=filtered_result["size_invalid_filenames"],
        )

    def get_original_report_record(
        self,
        report_record_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.EvidenceReportRecordOriginalResponse:
        report_record = self._get_report_record(report_record_id, db)
        self._check_access_permission(report_record, current_user, db)

        url = super()._get_presigned_url(
            s3_key=report_record.s3_key,
            expires_in=60 * 10,  # 10분
        )

        return schemas.EvidenceReportRecordOriginalResponse(
            report_record_id=report_record.report_record_id,
            filename=report_record.filename,
            content_type=report_record.content_type,
            size_bytes=report_record.size_bytes,
            url=url,
        )

    def update_filename(
        self,
        report_record_id: UUID,
        filename: str,
        current_user: AuthUser,
        db: Session,
    ) -> EvidenceReportRecord:
        return self.update_evidence_filename(
            report_record_id,
            filename,
            current_user,
            db,
            EvidenceReportRecordRepository(db),
        )

    def delete_report_record(
        self,
        report_record_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> None:
        self.delete_evidence_with_s3(
            report_record_id,
            current_user,
            db,
            EvidenceReportRecordRepository(db),
            s3_keys_fn=lambda e: [e.s3_key],
        )


evidence_report_record_service = EvidenceReportRecordService()
