from uuid import UUID

from sqlalchemy.orm import Session

from app.core.auth import AuthUser
from app.domain.complaint import Complaint
from app.domain.evidence import EvidenceTypeService
from app.domain.evidence.constant import EVIDENCE_REPORT_RECORD_RESTRICT
from app.domain.evidence.errors.register_validation_error import (
    raise_evidence_register_validation_failed,
)
from app.domain.evidence.utils import (
    check_register_max_count,
    fetch_s3_metadata_for_register,
)
from app.domain.evidence_report_record import schemas
from app.domain.evidence_report_record.models.evidence_report_record_model import (
    EvidenceReportRecord,
)
from app.domain.evidence_report_record.repos.evidence_report_record_repository import (
    EvidenceReportRecordRepository,
)
from app.domain.timeline.repos.timeline_repository import TimelineRepository


def _validate_report_record_register_restrict(metadata_list: list[dict]) -> None:
    """content_type 먼저, 통과한 것만 size. duration 없음."""
    restrict = EVIDENCE_REPORT_RECORD_RESTRICT
    content_type_failed_evidence_ids: list[str] = []
    size_bytes_failed_evidence_ids: list[str] = []

    for m in metadata_list:
        eid_str = str(m["report_record_id"])
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

    def register_report_record(
        self,
        complaint: Complaint,
        request: schemas.EvidenceReportRecordRegisterRequest,
        db: Session,
    ) -> schemas.EvidenceReportRecordRegisterListResponse:
        # 1) max_count 검사
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        check_register_max_count(
            total_count=total_count,
            request_count=len(request.items),
            restrict=EVIDENCE_REPORT_RECORD_RESTRICT,
            type_name="REPORT_RECORD",
        )
        # 2) S3 메타데이터 조회
        metadata_list = fetch_s3_metadata_for_register(
            complaint=complaint,
            items=request.items,
            path_segment="report-records",
            get_evidence_id=lambda item: item.report_record_id,
            build_extra=lambda item, s3_key, ct, size: {
                "report_record_id": item.report_record_id,
                "complaint_id": complaint.complaint_id,
                "filename": item.filename,
                "file_created_at": item.file_created_at,
            },
        )
        # 3) content_type, size 검증
        _validate_report_record_register_restrict(metadata_list)
        # 4) DB 저장
        rows = [
            {
                "report_record_id": m["report_record_id"],
                "complaint_id": m["complaint_id"],
                "filename": m["filename"],
                "s3_key": m["s3_key"],
                "content_type": m["content_type"],
                "size_bytes": m["size_bytes"],
                "file_created_at": m["file_created_at"],
            }
            for m in metadata_list
        ]

        db.bulk_insert_mappings(EvidenceReportRecord, rows)
        TimelineRepository(db).set_regeneration_flags(
            complaint.complaint_id, need_timeline_regeneration=True
        )
        db.commit()

        results = [
            schemas.EvidenceReportRecordRegisterItemResponse(
                report_record_id=r["report_record_id"],
                filename=r["filename"],
                content_type=r["content_type"],
                size_bytes=r["size_bytes"],
            )
            for r in rows
        ]
        return schemas.EvidenceReportRecordRegisterListResponse(items=results)

    def get_preview_report_records(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceReportRecordPreviewListResponse:
        report_records, total_count = self._get_limit_report_records_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        previews = [
            schemas.EvidenceReportRecordPreviewResponse(
                report_record_id=report_record.report_record_id,
                filename=report_record.filename,
                size_bytes=report_record.size_bytes,
            )
            for report_record in report_records
        ]

        return schemas.EvidenceReportRecordPreviewListResponse(
            previews=previews,
            total_count=total_count,
        )

    def get_detail_report_records(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceReportRecordDetailListResponse:
        report_records, total_count = self._get_limit_report_records_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        details = [
            schemas.EvidenceReportRecordDetailResponse(
                report_record_id=report_record.report_record_id,
                filename=report_record.filename,
                size_bytes=report_record.size_bytes,
                content_type=report_record.content_type,
                created_at=report_record.created_at,
                updated_at=report_record.updated_at,
            )
            for report_record in report_records
        ]

        return schemas.EvidenceReportRecordDetailListResponse(
            details=details,
            total_count=total_count,
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
            created_at=report_record.created_at,
            updated_at=report_record.updated_at,
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
        def s3_prefix_fn(e) -> str:
            base = e.s3_key.rsplit("/", 1)[0]
            return f"{base}/"

        self.delete_evidence_with_s3(
            report_record_id,
            current_user,
            db,
            EvidenceReportRecordRepository(db),
            s3_prefix_fn=s3_prefix_fn,
        )


evidence_report_record_service = EvidenceReportRecordService()
