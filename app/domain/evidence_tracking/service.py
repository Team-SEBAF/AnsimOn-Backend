from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.auth import AuthUser
from app.core.aws import download_s3_object, upload_fileobj
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence import EvidenceTypeService
from app.domain.evidence.constant import EVIDENCE_TRACKING_RESTRICT, EvidenceVariant
from app.domain.evidence.errors.register_validation_error import (
    raise_evidence_register_validation_failed,
)
from app.domain.evidence.utils import (
    check_register_max_count,
    fetch_s3_metadata_for_register,
)
from app.domain.evidence_tracking import schemas
from app.domain.evidence_tracking.models.evidence_tracking_model import EvidenceTracking
from app.domain.evidence_tracking.repos.evidence_tracking_repository import (
    EvidenceTrackingRepository,
)
from app.domain.evidence_tracking.utils import get_video_duration, get_video_image_at_0


def _collect_tracking_register_restrict_failures_from_metadata(
    metadata_list: list[dict],
) -> tuple[list[str], list[str], list[dict]]:
    """1차: metadata만으로 content_type, size 검사. raise 안 함.
    Returns: (content_type_failed, size_bytes_failed, valid_metadata)
    """
    restrict = EVIDENCE_TRACKING_RESTRICT
    content_type_failed_evidence_ids: list[str] = []
    size_bytes_failed_evidence_ids: list[str] = []
    valid_metadata: list[dict] = []

    for m in metadata_list:
        eid_str = str(m["tracking_id"])
        if m.get("content_type") not in restrict.allowed_types:
            content_type_failed_evidence_ids.append(eid_str)
            continue
        if m.get("size_bytes", 0) > restrict.max_size_bytes:
            size_bytes_failed_evidence_ids.append(eid_str)
            continue
        valid_metadata.append(m)

    return content_type_failed_evidence_ids, size_bytes_failed_evidence_ids, valid_metadata


def _raise_tracking_register_validation_if_failed(
    content_type_failed_evidence_ids: list[str],
    size_bytes_failed_evidence_ids: list[str],
    content_type_extraction_failed_evidence_ids: list[str],
    rows_with_duration: list[dict],
) -> None:
    """2차: 1차 failed + 추출 실패 + duration 검사. 모두 합쳐서 한 번에 raise."""
    restrict = EVIDENCE_TRACKING_RESTRICT
    duration_seconds_failed_evidence_ids: list[str] = []

    for r in rows_with_duration:
        if r.get("duration_seconds", 0) > (restrict.max_duration_seconds or 0):
            duration_seconds_failed_evidence_ids.append(str(r["tracking_id"]))

    content_type_total = (
        content_type_failed_evidence_ids + content_type_extraction_failed_evidence_ids
    )

    raise_evidence_register_validation_failed(
        content_type_failed_evidence_ids=content_type_total,
        size_bytes_failed_evidence_ids=size_bytes_failed_evidence_ids,
        duration_seconds_failed_evidence_ids=(
            duration_seconds_failed_evidence_ids if restrict.max_duration_seconds else None
        ),
    )


class EvidenceTrackingService(EvidenceTypeService):
    def _get_tracking(
        self,
        tracking_id: UUID,
        db: Session,
    ) -> EvidenceTracking:
        return super()._get_evidence(evidence_id=tracking_id, repo=EvidenceTrackingRepository(db))

    def _get_total_count(self, complaint_id: UUID, db: Session) -> int:
        repo = EvidenceTrackingRepository(db)
        return repo.count_by_complaint(complaint_id=complaint_id)

    def _get_limit_trackings_and_total_count(
        self,
        *,
        complaint: Complaint,
        limit: int,
        db: Session,
    ):
        repo = EvidenceTrackingRepository(db)

        # 최신순 조회
        trackings = repo.list_by_complaint(
            complaint_id=complaint.complaint_id,
            limit=limit,
        )

        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )

        return trackings, total_count

    def _check_access_permission(
        self, tracking: EvidenceTracking, current_user: AuthUser, db: Session
    ) -> None:
        return super()._check_access_permission(
            complaint_id=tracking.complaint_id,
            evidence_id=tracking.tracking_id,
            current_user=current_user,
            db=db,
        )

    def register_tracking(
        self,
        complaint: Complaint,
        request: schemas.EvidenceTrackingRegisterRequest,
        db: Session,
    ) -> schemas.EvidenceTrackingRegisterListResponse:
        # 1) max_count 검사
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        check_register_max_count(
            total_count=total_count,
            request_count=len(request.items),
            restrict=EVIDENCE_TRACKING_RESTRICT,
            type_name="TRACKING",
        )
        # 2) S3 메타데이터 조회
        metadata_list = fetch_s3_metadata_for_register(
            complaint=complaint,
            items=request.items,
            path_segment="trackings",
            get_evidence_id=lambda item: item.tracking_id,
            build_extra=lambda item, s3_key, ct, size: {
                "tracking_id": item.tracking_id,
                "complaint_id": complaint.complaint_id,
                "filename": item.filename,
            },
        )
        # 3) 1차 검증 (content_type, size) - failed 수집
        (
            content_type_failed_evidence_ids,
            size_bytes_failed_evidence_ids,
            valid_metadata,
        ) = _collect_tracking_register_restrict_failures_from_metadata(metadata_list)

        # 4) 다운로드 → duration 추출 (병렬)
        def _process_tracking_item(m: dict) -> tuple[dict | None, str | None]:
            file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
            try:
                duration_seconds = get_video_duration(file_bytes)
            except Exception:
                return None, str(m["tracking_id"])
            return {
                "tracking_id": m["tracking_id"],
                "complaint_id": m["complaint_id"],
                "filename": m["filename"],
                "s3_key": m["s3_key"],
                "content_type": m["content_type"],
                "size_bytes": m["size_bytes"],
                "duration_seconds": duration_seconds,
                "_file_bytes": file_bytes,
            }, None

        with ThreadPoolExecutor(max_workers=max(1, min(len(valid_metadata), 5))) as executor:
            results = list(executor.map(_process_tracking_item, valid_metadata))

        rows = [r for r, _ in results if r is not None]
        content_type_extraction_failed_evidence_ids = [eid for _, eid in results if eid is not None]
        # 5) 2차 검증 (duration) + 전체 실패 시 raise
        _raise_tracking_register_validation_if_failed(
            content_type_failed_evidence_ids=content_type_failed_evidence_ids,
            size_bytes_failed_evidence_ids=size_bytes_failed_evidence_ids,
            content_type_extraction_failed_evidence_ids=content_type_extraction_failed_evidence_ids,
            rows_with_duration=rows,
        )

        # 6) 썸네일/디테일 추출 → S3 업로드 (병렬)
        def _upload_tracking_thumbnails(r: dict) -> dict:
            file_bytes = r.pop("_file_bytes")
            base_key = r["s3_key"].rsplit("/", 1)[0]
            thumbnail_key = f"{base_key}/thumbnail"
            detail_key = f"{base_key}/detail"
            thumbnail_bytes, _, _ = get_video_image_at_0(file_bytes, size=120, quality=65)
            detail_bytes, _, _ = get_video_image_at_0(file_bytes, size=400, quality=75)
            upload_fileobj(
                fileobj=BytesIO(thumbnail_bytes),
                bucket=settings.S3_BUCKET_NAME,
                key=thumbnail_key,
                content_type="image/jpeg",
            )
            upload_fileobj(
                fileobj=BytesIO(detail_bytes),
                bucket=settings.S3_BUCKET_NAME,
                key=detail_key,
                content_type="image/jpeg",
            )
            return r

        with ThreadPoolExecutor(max_workers=max(1, min(len(rows), 5))) as executor:
            rows = list(executor.map(_upload_tracking_thumbnails, rows))
        # 7) DB 저장
        db.bulk_insert_mappings(EvidenceTracking, rows)
        db.commit()

        results = [
            schemas.EvidenceTrackingRegisterItemResponse(
                tracking_id=r["tracking_id"],
                filename=r["filename"],
                content_type=r["content_type"],
                duration_seconds=r["duration_seconds"],
                size_bytes=r["size_bytes"],
            )
            for r in rows
        ]
        return schemas.EvidenceTrackingRegisterListResponse(items=results)

    def get_preview_trackings(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceTrackingPreviewListResponse:
        trackings, total_count = self._get_limit_trackings_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        previews: list[schemas.EvidenceTrackingPreviewResponse] = []
        for tracking in trackings:
            s3_key_base = tracking.s3_key.rsplit("/", 1)[0]
            url = super()._get_presigned_url(
                s3_key=f"{s3_key_base}/{EvidenceVariant.THUMBNAIL.value}",
                expires_in=60 * 60,  # 1시간
            )
            previews.append(
                schemas.EvidenceTrackingPreviewResponse(
                    tracking_id=tracking.tracking_id,
                    duration_seconds=tracking.duration_seconds,
                    thumbnail_url=url,
                )
            )

        return schemas.EvidenceTrackingPreviewListResponse(
            previews=previews,
            total_count=total_count,
        )

    def get_detail_trackings(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceTrackingDetailListResponse:
        trackings, total_count = self._get_limit_trackings_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        details: list[schemas.EvidenceTrackingDetailResponse] = []
        for tracking in trackings:
            s3_key_base = tracking.s3_key.rsplit("/", 1)[0]
            url = super()._get_presigned_url(
                s3_key=f"{s3_key_base}/{EvidenceVariant.DETAIL.value}",
                expires_in=60 * 30,  # 30분
            )
            details.append(
                schemas.EvidenceTrackingDetailResponse(
                    tracking_id=tracking.tracking_id,
                    filename=tracking.filename,
                    duration_seconds=tracking.duration_seconds,
                    size_bytes=tracking.size_bytes,
                    created_at=tracking.created_at,
                    updated_at=tracking.updated_at,
                    thumbnail_url=url,
                )
            )
        return schemas.EvidenceTrackingDetailListResponse(
            details=details,
            total_count=total_count,
        )

    def get_original_tracking(
        self,
        tracking_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.EvidenceTrackingOriginalResponse:
        tracking = self._get_tracking(tracking_id, db)
        self._check_access_permission(tracking, current_user, db)

        url = super()._get_presigned_url(
            s3_key=tracking.s3_key,
            expires_in=60 * 10,  # 10분
        )

        return schemas.EvidenceTrackingOriginalResponse(
            tracking_id=tracking.tracking_id,
            filename=tracking.filename,
            content_type=tracking.content_type,
            size_bytes=tracking.size_bytes,
            duration_seconds=tracking.duration_seconds,
            url=url,
            created_at=tracking.created_at,
            updated_at=tracking.updated_at,
        )

    def update_filename(
        self,
        tracking_id: UUID,
        filename: str,
        current_user: AuthUser,
        db: Session,
    ) -> EvidenceTracking:
        return self.update_evidence_filename(
            tracking_id,
            filename,
            current_user,
            db,
            EvidenceTrackingRepository(db),
        )

    def delete_tracking(
        self,
        tracking_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> None:
        def s3_keys_fn(e: EvidenceTracking) -> list[str]:
            base = e.s3_key.rsplit("/", 1)[0]
            return [f"{base}/original", f"{base}/thumbnail", f"{base}/detail"]

        self.delete_evidence_with_s3(
            tracking_id,
            current_user,
            db,
            EvidenceTrackingRepository(db),
            s3_keys_fn=s3_keys_fn,
        )


evidence_tracking_service = EvidenceTrackingService()
