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
from app.domain.evidence.constant import EVIDENCE_VOICE_RESTRICT
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.utils import filter_evidence_files
from app.domain.evidence_voice import schemas
from app.domain.evidence_voice.models.evidence_voice_model import EvidenceVoice
from app.domain.evidence_voice.repos.evidence_voice_repository import EvidenceVoiceRepository


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

    def upload_voices(
        self,
        complaint: Complaint,
        files: list[UploadFile],
        db: Session,
    ) -> schemas.EvidenceVoiceUploadResponse:
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        if total_count >= EVIDENCE_VOICE_RESTRICT.max_count:
            raise CodeException(
                code=EvidenceMaxCountExceededErrorCode.EVIDENCE_MAX_COUNT_EXCEEDED,
                message=f"VOICE 타입 증거의 최대 개수({EVIDENCE_VOICE_RESTRICT.max_count}개)를 초과했습니다.",
                status_code=400,
            )

        evidence_voice_repo = EvidenceVoiceRepository(db)
        results: list[EvidenceVoice] = []

        # 음성 파일 필터링
        filtered_result = filter_evidence_files(
            files, EVIDENCE_VOICE_RESTRICT, need_audio_duration_check=True
        )
        valid_files = filtered_result["valid_files"]

        # 최대 개수 초과 체크
        available_count = EVIDENCE_VOICE_RESTRICT.max_count - total_count
        upload_files = valid_files[:available_count]

        count_invalid_files = valid_files[available_count:]
        count_invalid_filenames = [file.filename for file, _, _ in count_invalid_files]

        with ThreadPoolExecutor(max_workers=3) as executor:
            for file, file_bytes, duration_seconds in upload_files:
                # voice_id 생성
                voice_id = uuid4()

                s3_key = (
                    f"{complaint.user_sub}/complaints/"
                    f"{complaint.complaint_id}/evidences/voices/{voice_id}/original"
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
                voice = EvidenceVoice(
                    voice_id=voice_id,
                    complaint_id=complaint.complaint_id,
                    filename=file.filename,
                    s3_key=s3_key,
                    content_type=file.content_type,
                    size_bytes=len(file_bytes),
                    duration_seconds=duration_seconds,
                )

                evidence_voice_repo.create(voice)
                results.append(voice)

        db.commit()

        return schemas.EvidenceVoiceUploadResponse(
            voices=[
                schemas.EvidenceVoiceResponse(
                    voice_id=v.voice_id,
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
