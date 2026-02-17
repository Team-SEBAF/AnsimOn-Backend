from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.auth import AuthUser
from app.core.aws import download_s3_object
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence import EvidenceTypeService
from app.domain.evidence.constant import EVIDENCE_VOICE_RESTRICT
from app.domain.evidence.errors.register_validation_error import (
    raise_evidence_register_validation_failed,
)
from app.domain.evidence.utils import (
    check_register_max_count,
    fetch_s3_metadata_for_register,
)
from app.domain.evidence_voice import schemas
from app.domain.evidence_voice.models.evidence_voice_model import EvidenceVoice
from app.domain.evidence_voice.repos.evidence_voice_repository import EvidenceVoiceRepository
from app.domain.evidence_voice.utils import get_audio_duration


def _collect_voice_register_restrict_failures_from_metadata(
    metadata_list: list[dict],
) -> tuple[list[str], list[str], list[dict]]:
    """1차: metadata만으로 content_type, size 검사. raise 안 함.
    Returns: (content_type_failed, size_bytes_failed, valid_metadata)
    """
    restrict = EVIDENCE_VOICE_RESTRICT
    content_type_failed_evidence_ids: list[str] = []
    size_bytes_failed_evidence_ids: list[str] = []
    valid_metadata: list[dict] = []

    for m in metadata_list:
        eid_str = str(m["voice_id"])
        if m.get("content_type") not in restrict.allowed_types:
            content_type_failed_evidence_ids.append(eid_str)
            continue
        if m.get("size_bytes", 0) > restrict.max_size_bytes:
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
    """2차: 1차 failed + 추출 실패 + duration 검사. 모두 합쳐서 한 번에 raise."""
    restrict = EVIDENCE_VOICE_RESTRICT
    duration_seconds_failed_evidence_ids: list[str] = []

    for r in rows_with_duration:
        if r.get("duration_seconds", 0) > (restrict.max_duration_seconds or 0):
            duration_seconds_failed_evidence_ids.append(str(r["voice_id"]))

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

        # 4) 다운로드 → duration 추출 (병렬)
        def _process_voice_item(m: dict) -> tuple[dict | None, str | None]:
            file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
            try:
                duration_seconds = get_audio_duration(file_bytes)
            except (ValueError, TypeError):
                return None, str(m["voice_id"])
            return {
                "voice_id": m["voice_id"],
                "complaint_id": m["complaint_id"],
                "filename": m["filename"],
                "s3_key": m["s3_key"],
                "content_type": m["content_type"],
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
                duration_seconds=voice.duration_seconds,
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
                filename=voice.filename,
                duration_seconds=voice.duration_seconds,
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
            duration_seconds=voice.duration_seconds,
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
        self.delete_evidence_with_s3(
            voice_id,
            current_user,
            db,
            EvidenceVoiceRepository(db),
            s3_keys_fn=lambda e: [e.s3_key],
        )


evidence_voice_service = EvidenceVoiceService()
