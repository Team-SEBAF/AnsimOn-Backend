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
from app.domain.evidence.constant import EVIDENCE_TRACKING_RESTRICT, EvidenceVariant
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.utils import filter_evidence_files, get_video_image_at_0
from app.domain.evidence_tracking import schemas
from app.domain.evidence_tracking.models.evidence_tracking_model import EvidenceTracking
from app.domain.evidence_tracking.repos.evidence_tracking_repository import (
    EvidenceTrackingRepository,
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

    def upload_trackings(
        self,
        complaint: Complaint,
        files: list[UploadFile],
        db: Session,
    ) -> schemas.EvidenceTrackingUploadResponse:
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        if total_count >= EVIDENCE_TRACKING_RESTRICT.max_count:
            raise CodeException(
                code=EvidenceMaxCountExceededErrorCode.EVIDENCE_MAX_COUNT_EXCEEDED,
                message=f"TRACKING 타입 증거의 최대 개수({EVIDENCE_TRACKING_RESTRICT.max_count}개)를 초과했습니다.",
                status_code=400,
            )

        evidence_tracking_repo = EvidenceTrackingRepository(db)
        results: list[EvidenceTracking] = []

        # 음성 파일 필터링
        filtered_result = filter_evidence_files(
            files, EVIDENCE_TRACKING_RESTRICT, need_video_duration_check=True
        )
        valid_files = filtered_result["valid_files"]

        # 최대 개수 초과 체크
        available_count = EVIDENCE_TRACKING_RESTRICT.max_count - total_count
        upload_files = valid_files[:available_count]

        count_invalid_files = valid_files[available_count:]
        count_invalid_filenames = [file.filename for file, _, _ in count_invalid_files]

        with ThreadPoolExecutor(max_workers=3) as executor:
            for file, file_bytes, duration_seconds in upload_files:
                tracking_id = uuid4()

                base_key = (
                    f"{complaint.user_sub}/complaints/"
                    f"{complaint.complaint_id}/evidences/trackings/{tracking_id}"
                )

                original_key = f"{base_key}/original"
                thumbnail_key = f"{base_key}/thumbnail"
                detail_key = f"{base_key}/detail"

                thumbnail_bytes, _, _ = get_video_image_at_0(file_bytes, size=120, quality=65)
                detail_bytes, _, _ = get_video_image_at_0(file_bytes, size=400, quality=75)

                futures = [
                    executor.submit(
                        upload_fileobj,
                        fileobj=BytesIO(file_bytes),
                        bucket=settings.S3_BUCKET_NAME,
                        key=original_key,
                        content_type=file.content_type,
                    ),
                    executor.submit(
                        upload_fileobj,
                        fileobj=BytesIO(thumbnail_bytes),
                        bucket=settings.S3_BUCKET_NAME,
                        key=thumbnail_key,
                        content_type="image/jpeg",
                    ),
                    executor.submit(
                        upload_fileobj,
                        fileobj=BytesIO(detail_bytes),
                        bucket=settings.S3_BUCKET_NAME,
                        key=detail_key,
                        content_type="image/jpeg",
                    ),
                ]

                for future in futures:
                    future.result()

                tracking = EvidenceTracking(
                    tracking_id=tracking_id,
                    complaint_id=complaint.complaint_id,
                    filename=file.filename,
                    s3_key=original_key,
                    content_type=file.content_type,
                    size_bytes=len(file_bytes),
                    duration_seconds=duration_seconds,
                )

                evidence_tracking_repo.create(tracking)
                results.append(tracking)

        db.commit()

        return schemas.EvidenceTrackingUploadResponse(
            trackings=[
                schemas.EvidenceTrackingResponse(
                    tracking_id=v.tracking_id,
                    filename=v.filename,
                    duration_seconds=v.duration_seconds,
                    size_bytes=v.size_bytes,
                    created_at=v.created_at,
                    updated_at=v.updated_at,
                )
                for v in results
            ],
            type_invalid_filenames=filtered_result["type_invalid_filenames"],
            count_invalid_filenames=count_invalid_filenames,
            size_invalid_filenames=filtered_result["size_invalid_filenames"],
            duration_invalid_filenames=filtered_result["duration_invalid_filenames"],
        )

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
