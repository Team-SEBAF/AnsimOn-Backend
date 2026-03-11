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
    EVIDENCE_VOICE_AUDIO_RESTRICT,
    EVIDENCE_VOICE_IMAGE_RESTRICT,
    EVIDENCE_VOICE_RESTRICT,
    get_file_type_from_content_type,
)
from app.domain.evidence.errors.register_validation_error import (
    raise_evidence_register_validation_failed,
)
from app.domain.evidence.utils import (
    check_register_max_count,
    fetch_s3_metadata_for_register,
)
from app.domain.evidence_message.utils import extract_image_meta, make_image_top_crop
from app.domain.evidence_voice import schemas
from app.domain.evidence_voice.models.evidence_voice_model import EvidenceVoice
from app.domain.evidence_voice.repos.evidence_voice_repository import EvidenceVoiceRepository
from app.domain.evidence_voice.utils import get_audio_duration


def _collect_voice_register_restrict_failures_from_metadata(
    metadata_list: list[dict],
) -> tuple[list[str], list[str], list[dict]]:
    """1차: metadata만으로 content_type, size 검사. raise 안 함.
    Returns: (content_type_failed, size_bytes_failed, valid_metadata)
    음성: 20MB, 이미지: 10MB (MESSAGE와 동일)
    """
    content_type_failed_evidence_ids: list[str] = []
    size_bytes_failed_evidence_ids: list[str] = []
    valid_metadata: list[dict] = []

    for m in metadata_list:
        eid_str = str(m["voice_id"])
        ct = m.get("content_type")
        if ct not in (
            EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types
            | EVIDENCE_VOICE_IMAGE_RESTRICT.allowed_types
        ):
            content_type_failed_evidence_ids.append(eid_str)
            continue
        size = m.get("size_bytes", 0)
        if ct in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types:
            max_size = EVIDENCE_VOICE_AUDIO_RESTRICT.max_size_bytes
        else:
            max_size = EVIDENCE_VOICE_IMAGE_RESTRICT.max_size_bytes
        if size > max_size:
            size_bytes_failed_evidence_ids.append(eid_str)
            continue
        valid_metadata.append(m)

    return content_type_failed_evidence_ids, size_bytes_failed_evidence_ids, valid_metadata


def _raise_voice_register_validation_if_failed(
    content_type_failed_evidence_ids: list[str],
    size_bytes_failed_evidence_ids: list[str],
    content_type_extraction_failed_evidence_ids: list[str],
    rows_with_duration: list[dict],
) -> None:
    """2차: 1차 failed + 추출 실패 + duration 검사. duration은 음성에만 적용."""
    duration_seconds_failed_evidence_ids: list[str] = []

    for r in rows_with_duration:
        if r.get("content_type") in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types:
            dur = r.get("duration_seconds", 0)
            if dur > (EVIDENCE_VOICE_AUDIO_RESTRICT.max_duration_seconds or 0):
                duration_seconds_failed_evidence_ids.append(str(r["voice_id"]))

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


class EvidenceVoiceService(EvidenceTypeService):
    def _get_voice(
        self,
        voice_id: UUID,
        db: Session,
    ) -> EvidenceVoice:
        return super()._get_evidence(evidence_id=voice_id, repo=EvidenceVoiceRepository(db))

    def _get_total_count(self, complaint_id: UUID, db: Session) -> int:
        repo = EvidenceVoiceRepository(db)
        return repo.count_by_complaint(complaint_id=complaint_id)

    def _get_limit_voices_and_total_count(
        self,
        *,
        complaint: Complaint,
        limit: int,
        db: Session,
    ):
        repo = EvidenceVoiceRepository(db)

        # 최신순 조회
        voices = repo.list_by_complaint(
            complaint_id=complaint.complaint_id,
            limit=limit,
        )

        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )

        return voices, total_count

    def _check_access_permission(
        self, voice: EvidenceVoice, current_user: AuthUser, db: Session
    ) -> None:
        return super()._check_access_permission(
            complaint_id=voice.complaint_id,
            evidence_id=voice.voice_id,
            current_user=current_user,
            db=db,
        )

    def register_voice(
        self,
        complaint: Complaint,
        request: schemas.EvidenceVoiceRegisterRequest,
        db: Session,
    ) -> schemas.EvidenceVoiceRegisterListResponse:
        # 1) max_count 검사
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        check_register_max_count(
            total_count=total_count,
            request_count=len(request.items),
            restrict=EVIDENCE_VOICE_RESTRICT,
            type_name="VOICE",
        )
        # 2) S3 메타데이터 조회
        metadata_list = fetch_s3_metadata_for_register(
            complaint=complaint,
            items=request.items,
            path_segment="voices",
            get_evidence_id=lambda item: item.voice_id,
            build_extra=lambda item, s3_key, ct, size: {
                "voice_id": item.voice_id,
                "complaint_id": complaint.complaint_id,
                "filename": item.filename,
            },
        )
        # 3) 1차 검증 (content_type, size) - failed 수집
        (
            content_type_failed_evidence_ids,
            size_bytes_failed_evidence_ids,
            valid_metadata,
        ) = _collect_voice_register_restrict_failures_from_metadata(metadata_list)

        # 4) 다운로드 → duration 추출 (병렬). 이미지는 duration=0, 검증용 extract_image_meta + detail S3 업로드
        def _process_voice_item(m: dict) -> tuple[dict | None, str | None]:
            file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
            ct = m["content_type"]
            if ct in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types:
                try:
                    duration_seconds = get_audio_duration(file_bytes)
                except (ValueError, TypeError):
                    return None, str(m["voice_id"])
            else:
                try:
                    extract_image_meta(file_bytes)
                except Exception:
                    return None, str(m["voice_id"])
                duration_seconds = 0
                # 이미지: detail 추출 후 S3 업로드 (message/victim과 동일)
                base_key = m["s3_key"].rsplit("/", 1)[0]
                detail_key = f"{base_key}/detail"
                detail_bytes, _, _ = make_image_top_crop(
                    file_bytes=file_bytes, size=400, quality=75
                )
                upload_fileobj(
                    fileobj=BytesIO(detail_bytes),
                    bucket=settings.S3_BUCKET_NAME,
                    key=detail_key,
                    content_type="image/jpeg",
                )
            return {
                "voice_id": m["voice_id"],
                "complaint_id": m["complaint_id"],
                "filename": m["filename"],
                "s3_key": m["s3_key"],
                "content_type": ct,
                "size_bytes": m["size_bytes"],
                "duration_seconds": duration_seconds,
            }, None

        with ThreadPoolExecutor(max_workers=max(1, min(len(valid_metadata), 5))) as executor:
            results = list(executor.map(_process_voice_item, valid_metadata))

        rows = [r for r, _ in results if r is not None]
        content_type_extraction_failed_evidence_ids = [eid for _, eid in results if eid is not None]
        # 5) 2차 검증 (duration) + 전체 실패 시 raise
        _raise_voice_register_validation_if_failed(
            content_type_failed_evidence_ids=content_type_failed_evidence_ids,
            size_bytes_failed_evidence_ids=size_bytes_failed_evidence_ids,
            content_type_extraction_failed_evidence_ids=content_type_extraction_failed_evidence_ids,
            rows_with_duration=rows,
        )
        # 6) DB 저장
        db.bulk_insert_mappings(EvidenceVoice, rows)
        db.commit()

        results = [
            schemas.EvidenceVoiceRegisterItemResponse(
                voice_id=r["voice_id"],
                filename=r["filename"],
                content_type=r["content_type"],
                duration_seconds=r["duration_seconds"],
                size_bytes=r["size_bytes"],
            )
            for r in rows
        ]
        return schemas.EvidenceVoiceRegisterListResponse(items=results)

    def get_preview_voices(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceVoicePreviewListResponse:
        voices, total_count = self._get_limit_voices_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        previews = [
            schemas.EvidenceVoicePreviewResponse(
                voice_id=voice.voice_id,
                filename=voice.filename,
                duration_seconds=voice.duration_seconds or 0,
            )
            for voice in voices
        ]

        return schemas.EvidenceVoicePreviewListResponse(
            previews=previews,
            total_count=total_count,
        )

    def get_detail_voices(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceVoiceDetailListResponse:
        voices, total_count = self._get_limit_voices_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        details = [
            schemas.EvidenceVoiceDetailResponse(
                voice_id=voice.voice_id,
                type=get_file_type_from_content_type(voice.content_type).value,
                filename=voice.filename,
                duration_seconds=voice.duration_seconds or 0,
                size_bytes=voice.size_bytes,
                created_at=voice.created_at,
                updated_at=voice.updated_at,
            )
            for voice in voices
        ]
        return schemas.EvidenceVoiceDetailListResponse(
            details=details,
            total_count=total_count,
        )

    def get_original_voice(
        self,
        voice_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.EvidenceVoiceOriginalResponse:
        voice = self._get_voice(voice_id, db)
        self._check_access_permission(voice, current_user, db)

        url = super()._get_presigned_url(
            s3_key=voice.s3_key,
            expires_in=60 * 10,  # 10분
        )

        return schemas.EvidenceVoiceOriginalResponse(
            voice_id=voice.voice_id,
            filename=voice.filename,
            content_type=voice.content_type,
            size_bytes=voice.size_bytes,
            duration_seconds=voice.duration_seconds or 0,
            url=url,
            created_at=voice.created_at,
            updated_at=voice.updated_at,
        )

    def update_filename(
        self,
        voice_id: UUID,
        filename: str,
        current_user: AuthUser,
        db: Session,
    ) -> EvidenceVoice:
        return self.update_evidence_filename(
            voice_id,
            filename,
            current_user,
            db,
            EvidenceVoiceRepository(db),
        )

    def delete_voice(
        self,
        voice_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> None:
        def s3_prefix_fn(e) -> str:
            base = e.s3_key.rsplit("/", 1)[0]
            return f"{base}/"

        self.delete_evidence_with_s3(
            voice_id,
            current_user,
            db,
            EvidenceVoiceRepository(db),
            s3_prefix_fn=s3_prefix_fn,
        )


evidence_voice_service = EvidenceVoiceService()
