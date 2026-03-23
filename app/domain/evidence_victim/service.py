from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.auth import AuthUser
from app.core.aws import download_s3_object, upload_fileobj
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence import EvidenceTypeService
from app.domain.evidence.constant import (
    EVIDENCE_VICTIM_IMAGE_RESTRICT,
    EVIDENCE_VICTIM_RESTRICT,
    EVIDENCE_VICTIM_VIDEO_RESTRICT,
    EvidenceVariant,
    get_file_type_from_content_type,
)
from app.domain.evidence.errors.register_validation_error import (
    raise_evidence_register_validation_failed,
)
from app.domain.evidence.utils import (
    check_register_max_count,
    fetch_s3_metadata_for_register,
)
from app.domain.evidence_message.utils import make_image_top_crop
from app.domain.evidence_victim import schemas
from app.domain.evidence_victim.models.evidence_victim_model import EvidenceVictim
from app.domain.evidence_victim.repos.evidence_victim_repository import (
    EvidenceVictimRepository,
)
from app.domain.evidence_victim.utils import get_video_duration, get_video_image_at_0
from app.domain.timeline.repos.timeline_repository import TimelineRepository


def _collect_victim_register_restrict_failures_from_metadata(
    metadata_list: list[dict],
) -> tuple[list[str], list[str], list[dict]]:
    """1차: metadata만으로 content_type, size 검사. raise 안 함.
    Returns: (content_type_failed, size_bytes_failed, valid_metadata)
    영상: 500MB, 이미지: 10MB (MESSAGE와 동일)
    """
    content_type_failed_evidence_ids: list[str] = []
    size_bytes_failed_evidence_ids: list[str] = []
    valid_metadata: list[dict] = []

    for m in metadata_list:
        eid_str = str(m["victim_id"])
        ct = m.get("content_type")
        if ct not in (
            EVIDENCE_VICTIM_VIDEO_RESTRICT.allowed_types
            | EVIDENCE_VICTIM_IMAGE_RESTRICT.allowed_types
        ):
            content_type_failed_evidence_ids.append(eid_str)
            continue
        size = m.get("size_bytes", 0)
        if ct in EVIDENCE_VICTIM_VIDEO_RESTRICT.allowed_types:
            max_size = EVIDENCE_VICTIM_VIDEO_RESTRICT.max_size_bytes
        else:
            max_size = EVIDENCE_VICTIM_IMAGE_RESTRICT.max_size_bytes
        if size > max_size:
            size_bytes_failed_evidence_ids.append(eid_str)
            continue
        valid_metadata.append(m)

    return content_type_failed_evidence_ids, size_bytes_failed_evidence_ids, valid_metadata


def _raise_victim_register_validation_if_failed(
    content_type_failed_evidence_ids: list[str],
    size_bytes_failed_evidence_ids: list[str],
    content_type_extraction_failed_evidence_ids: list[str],
    rows_with_duration: list[dict],
) -> None:
    """2차: 1차 failed + 추출 실패 + duration 검사. duration은 영상에만 적용."""
    duration_seconds_failed_evidence_ids: list[str] = []

    for r in rows_with_duration:
        if r.get("content_type") in EVIDENCE_VICTIM_VIDEO_RESTRICT.allowed_types:
            dur = r.get("duration_seconds", 0)
            if dur > (EVIDENCE_VICTIM_VIDEO_RESTRICT.max_duration_seconds or 0):
                duration_seconds_failed_evidence_ids.append(str(r["victim_id"]))

    content_type_total = (
        content_type_failed_evidence_ids + content_type_extraction_failed_evidence_ids
    )

    raise_evidence_register_validation_failed(
        content_type_failed_evidence_ids=content_type_total,
        size_bytes_failed_evidence_ids=size_bytes_failed_evidence_ids,
        duration_seconds_failed_evidence_ids=(
            duration_seconds_failed_evidence_ids if duration_seconds_failed_evidence_ids else None
        ),
    )


class EvidenceVictimService(EvidenceTypeService):
    def _get_victim(
        self,
        victim_id: UUID,
        db: Session,
    ) -> EvidenceVictim:
        return super()._get_evidence(evidence_id=victim_id, repo=EvidenceVictimRepository(db))

    def _get_total_count(self, complaint_id: UUID, db: Session) -> int:
        repo = EvidenceVictimRepository(db)
        return repo.count_by_complaint(complaint_id=complaint_id)

    def _get_limit_victims_and_total_count(
        self,
        *,
        complaint: Complaint,
        limit: int,
        db: Session,
    ):
        repo = EvidenceVictimRepository(db)

        victims = repo.list_by_complaint(
            complaint_id=complaint.complaint_id,
            limit=limit,
        )

        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )

        return victims, total_count

    def _check_access_permission(
        self, victim: EvidenceVictim, current_user: AuthUser, db: Session
    ) -> None:
        return super()._check_access_permission(
            complaint_id=victim.complaint_id,
            evidence_id=victim.victim_id,
            current_user=current_user,
            db=db,
        )

    def register_victim(
        self,
        complaint: Complaint,
        request: schemas.EvidenceVictimRegisterRequest,
        db: Session,
    ) -> schemas.EvidenceVictimRegisterListResponse:
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        check_register_max_count(
            total_count=total_count,
            request_count=len(request.items),
            restrict=EVIDENCE_VICTIM_RESTRICT,
            type_name="VICTIM",
        )
        metadata_list = fetch_s3_metadata_for_register(
            complaint=complaint,
            items=request.items,
            path_segment="victims",
            get_evidence_id=lambda item: item.victim_id,
            build_extra=lambda item, s3_key, ct, size: {
                "victim_id": item.victim_id,
                "complaint_id": complaint.complaint_id,
                "filename": item.filename,
            },
        )
        (
            content_type_failed_evidence_ids,
            size_bytes_failed_evidence_ids,
            valid_metadata,
        ) = _collect_victim_register_restrict_failures_from_metadata(metadata_list)

        def _process_victim_item(m: dict) -> tuple[dict | None, str | None]:
            file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
            ct = m["content_type"]
            if ct in EVIDENCE_VICTIM_VIDEO_RESTRICT.allowed_types:
                try:
                    duration_seconds = get_video_duration(file_bytes)
                except Exception:
                    return None, str(m["victim_id"])
            else:
                duration_seconds = 0
            return {
                "victim_id": m["victim_id"],
                "complaint_id": m["complaint_id"],
                "filename": m["filename"],
                "s3_key": m["s3_key"],
                "content_type": ct,
                "size_bytes": m["size_bytes"],
                "duration_seconds": duration_seconds,
                "_file_bytes": file_bytes,
            }, None

        with ThreadPoolExecutor(max_workers=max(1, min(len(valid_metadata), 5))) as executor:
            results = list(executor.map(_process_victim_item, valid_metadata))

        rows = [r for r, _ in results if r is not None]
        content_type_extraction_failed_evidence_ids = [eid for _, eid in results if eid is not None]
        _raise_victim_register_validation_if_failed(
            content_type_failed_evidence_ids=content_type_failed_evidence_ids,
            size_bytes_failed_evidence_ids=size_bytes_failed_evidence_ids,
            content_type_extraction_failed_evidence_ids=content_type_extraction_failed_evidence_ids,
            rows_with_duration=rows,
        )

        def _upload_victim_thumbnails(r: dict) -> dict:
            file_bytes = r.pop("_file_bytes")
            base_key = r["s3_key"].rsplit("/", 1)[0]
            thumbnail_key = f"{base_key}/thumbnail"
            detail_key = f"{base_key}/detail"
            if r["content_type"] in EVIDENCE_VICTIM_VIDEO_RESTRICT.allowed_types:
                thumbnail_bytes, _, _ = get_video_image_at_0(file_bytes, size=120, quality=65)
                detail_bytes, _, _ = get_video_image_at_0(file_bytes, size=400, quality=75)
            else:
                thumbnail_bytes, _, _ = make_image_top_crop(
                    file_bytes=file_bytes, size=120, quality=65
                )
                detail_bytes, _, _ = make_image_top_crop(
                    file_bytes=file_bytes, size=400, quality=75
                )
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
            rows = list(executor.map(_upload_victim_thumbnails, rows))
        db.bulk_insert_mappings(EvidenceVictim, rows)
        TimelineRepository(db).set_regeneration_flags(
            complaint.complaint_id, need_timeline_regeneration=True
        )
        db.commit()

        results = [
            schemas.EvidenceVictimRegisterItemResponse(
                victim_id=r["victim_id"],
                filename=r["filename"],
                content_type=r["content_type"],
                duration_seconds=r["duration_seconds"],
                size_bytes=r["size_bytes"],
            )
            for r in rows
        ]
        return schemas.EvidenceVictimRegisterListResponse(items=results)

    def get_preview_victims(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceVictimPreviewListResponse:
        victims, total_count = self._get_limit_victims_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        previews: list[schemas.EvidenceVictimPreviewResponse] = []
        for victim in victims:
            s3_key_base = victim.s3_key.rsplit("/", 1)[0]
            url = super()._get_presigned_url(
                s3_key=f"{s3_key_base}/{EvidenceVariant.THUMBNAIL.value}",
                expires_in=60 * 60,
            )
            previews.append(
                schemas.EvidenceVictimPreviewResponse(
                    victim_id=victim.victim_id,
                    duration_seconds=victim.duration_seconds or 0,
                    thumbnail_url=url,
                )
            )

        return schemas.EvidenceVictimPreviewListResponse(
            previews=previews,
            total_count=total_count,
        )

    def get_detail_victims(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceVictimDetailListResponse:
        victims, total_count = self._get_limit_victims_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        details: list[schemas.EvidenceVictimDetailResponse] = []
        for victim in victims:
            s3_key_base = victim.s3_key.rsplit("/", 1)[0]
            url = super()._get_presigned_url(
                s3_key=f"{s3_key_base}/{EvidenceVariant.DETAIL.value}",
                expires_in=60 * 30,
            )
            dur = victim.duration_seconds or 0
            details.append(
                schemas.EvidenceVictimDetailResponse(
                    victim_id=victim.victim_id,
                    type=get_file_type_from_content_type(victim.content_type).value,
                    filename=victim.filename,
                    duration_seconds=dur,
                    size_bytes=victim.size_bytes,
                    created_at=victim.created_at,
                    updated_at=victim.updated_at,
                    thumbnail_url=url,
                )
            )
        return schemas.EvidenceVictimDetailListResponse(
            details=details,
            total_count=total_count,
        )

    def get_original_victim(
        self,
        victim_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.EvidenceVictimOriginalResponse:
        victim = self._get_victim(victim_id, db)
        self._check_access_permission(victim, current_user, db)

        url = super()._get_presigned_url(
            s3_key=victim.s3_key,
            expires_in=60 * 10,
        )

        return schemas.EvidenceVictimOriginalResponse(
            victim_id=victim.victim_id,
            filename=victim.filename,
            content_type=victim.content_type,
            size_bytes=victim.size_bytes,
            duration_seconds=victim.duration_seconds or 0,
            url=url,
            created_at=victim.created_at,
            updated_at=victim.updated_at,
        )

    def update_filename(
        self,
        victim_id: UUID,
        filename: str,
        current_user: AuthUser,
        db: Session,
    ) -> EvidenceVictim:
        return self.update_evidence_filename(
            victim_id,
            filename,
            current_user,
            db,
            EvidenceVictimRepository(db),
        )

    def delete_victim(
        self,
        victim_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> None:
        def s3_prefix_fn(e: EvidenceVictim) -> str:
            base = e.s3_key.rsplit("/", 1)[0]
            return f"{base}/"

        self.delete_evidence_with_s3(
            victim_id,
            current_user,
            db,
            EvidenceVictimRepository(db),
            s3_prefix_fn=s3_prefix_fn,
        )


evidence_victim_service = EvidenceVictimService()
