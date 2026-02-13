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
from app.domain.evidence.constant import EVIDENCE_MESSAGE_RESTRICT, EvidenceVariant
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.utils import filter_evidence_files
from app.domain.evidence_message import schemas

from .models.evidence_message_model import EvidenceMessage
from .repos.evidence_message_repository import EvidenceMessageRepository
from .utils import extract_image_meta, make_image_top_crop


class EvidenceMessageService(EvidenceTypeService):
    def _get_message(
        self,
        message_id: UUID,
        db: Session,
    ) -> EvidenceMessage:
        return super()._get_evidence(evidence_id=message_id, repo=EvidenceMessageRepository(db))

    def _get_total_count(self, complaint_id: UUID, db: Session) -> int:
        repo = EvidenceMessageRepository(db)
        return repo.count_by_complaint(complaint_id=complaint_id)

    def _get_limit_messages_and_total_count(
        self,
        *,
        complaint: Complaint,
        limit: int,
        db: Session,
    ):
        repo = EvidenceMessageRepository(db)

        # 최신순 썸네일 대상 조회
        messages = repo.list_by_complaint(
            complaint_id=complaint.complaint_id,
            limit=limit,
        )

        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )

        return messages, total_count

    def _check_access_permission(
        self, message: EvidenceMessage, current_user: AuthUser, db: Session
    ) -> None:
        return super()._check_access_permission(
            complaint_id=message.complaint_id,
            evidence_id=message.message_id,
            current_user=current_user,
            db=db,
        )

    def upload_images(
        self,
        complaint: Complaint,
        files: list[UploadFile],
        db: Session,
    ) -> schemas.EvidenceMessageUploadResponse:
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        if total_count >= EVIDENCE_MESSAGE_RESTRICT.max_count:
            raise CodeException(
                code=EvidenceMaxCountExceededErrorCode.EVIDENCE_MAX_COUNT_EXCEEDED,
                message=f"MESSAGE 타입 증거의 최대 개수({EVIDENCE_MESSAGE_RESTRICT.max_count}개)를 초과했습니다.",
                status_code=400,
            )

        evidence_message_repo = EvidenceMessageRepository(db)
        results: list[EvidenceMessage] = []

        # 이미지 파일 필터링
        filtered_result = filter_evidence_files(files, EVIDENCE_MESSAGE_RESTRICT)
        valid_files = filtered_result["valid_files"]

        # 최대 개수 초과 체크
        available_count = EVIDENCE_MESSAGE_RESTRICT.max_count - total_count
        upload_files = valid_files[:available_count]

        count_invalid_files = valid_files[available_count:]
        count_invalid_filenames = [file.filename for file in count_invalid_files]

        with ThreadPoolExecutor(max_workers=3) as executor:
            for file in upload_files:
                # 파일 바이트 읽기 (1회)
                file_bytes = file.file.read()

                # 원본 이미지 메타데이터
                width, height = extract_image_meta(file_bytes)

                # message_id 생성
                message_id = uuid4()

                base_key = (
                    f"{complaint.user_sub}/complaints/"
                    f"{complaint.complaint_id}/evidences/messages/{message_id}"
                )

                original_key = f"{base_key}/original"
                thumbnail_key = f"{base_key}/thumbnail"
                detail_key = f"{base_key}/detail"

                # 파생 이미지 생성
                thumbnail_bytes, _, _ = make_image_top_crop(
                    file_bytes=file_bytes,
                    size=120,
                    quality=65,
                )

                detail_bytes, _, _ = make_image_top_crop(
                    file_bytes=file_bytes,
                    size=400,
                    quality=75,
                )

                # S3 업로드 (병렬)
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

                # 업로드 실패 시 예외 전파
                for future in futures:
                    future.result()

                # DB row 생성 (original 기준)
                message = EvidenceMessage(
                    message_id=message_id,
                    complaint_id=complaint.complaint_id,
                    filename=file.filename,
                    s3_key=original_key,
                    content_type=file.content_type,
                    size_bytes=len(file_bytes),
                    width=width,
                    height=height,
                )

                evidence_message_repo.create(message)
                results.append(message)

        db.commit()

        return schemas.EvidenceMessageUploadResponse(
            messages=[
                schemas.EvidenceMessageResponse(
                    message_id=m.message_id,
                    filename=m.filename,
                    width=m.width,
                    height=m.height,
                    size_bytes=m.size_bytes,
                )
                for m in results
            ],
            type_invalid_filenames=filtered_result["type_invalid_filenames"],
            count_invalid_filenames=count_invalid_filenames,
            size_invalid_filenames=filtered_result["size_invalid_filenames"],
        )

    def get_thumbnail_images(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceMessageThumbnailListResponse:
        messages, total_count = self._get_limit_messages_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        thumbnails: list[schemas.EvidenceMessageThumbnailResponse] = []
        for message in messages:
            s3_key_base = message.s3_key.rsplit("/", 1)[0]
            url = super()._get_presigned_url(
                s3_key=f"{s3_key_base}/{EvidenceVariant.THUMBNAIL.value}",
                expires_in=60 * 60,  # 1시간
            )
            thumbnails.append(
                schemas.EvidenceMessageThumbnailResponse(
                    message_id=message.message_id,
                    url=url,
                )
            )

        return schemas.EvidenceMessageThumbnailListResponse(
            thumbnails=thumbnails,
            total_count=total_count,
        )

    def get_detail_images(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceMessageDetailListResponse:
        messages, total_count = self._get_limit_messages_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        details: list[schemas.EvidenceMessageDetailResponse] = []
        for message in messages:
            s3_key_base = message.s3_key.rsplit("/", 1)[0]
            url = super()._get_presigned_url(
                s3_key=f"{s3_key_base}/{EvidenceVariant.DETAIL.value}",
                expires_in=60 * 30,  # 30분
            )
            details.append(
                schemas.EvidenceMessageDetailResponse(
                    message_id=message.message_id,
                    filename=message.filename,
                    size_bytes=message.size_bytes,
                    created_at=message.created_at,
                    updated_at=message.updated_at,
                    url=url,
                )
            )
        return schemas.EvidenceMessageDetailListResponse(
            details=details,
            total_count=total_count,
        )

    def get_original_image(
        self,
        message_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.EvidenceMessageOriginalImageResponse:
        message = self._get_message(message_id, db)
        self._check_access_permission(message, current_user, db)

        s3_key = f"{message.s3_key}"

        url = super()._get_presigned_url(
            s3_key=s3_key,
            expires_in=60 * 10,  # 10분
        )

        return schemas.EvidenceMessageOriginalImageResponse(
            message_id=message.message_id,
            filename=message.filename,
            content_type=message.content_type,
            size_bytes=message.size_bytes,
            width=message.width,
            height=message.height,
            url=url,
        )

    def update_filename(
        self,
        message_id: UUID,
        filename: str,
        current_user: AuthUser,
        db: Session,
    ) -> EvidenceMessage:
        return self.update_evidence_filename(
            message_id,
            filename,
            current_user,
            db,
            EvidenceMessageRepository(db),
        )

    def delete_message(
        self,
        message_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> None:
        def s3_keys_fn(e: EvidenceMessage) -> list[str]:
            base = e.s3_key.rsplit("/", 1)[0]
            return [f"{base}/original", f"{base}/thumbnail", f"{base}/detail"]

        self.delete_evidence_with_s3(
            message_id,
            current_user,
            db,
            EvidenceMessageRepository(db),
            s3_keys_fn=s3_keys_fn,
        )


evidence_message_service = EvidenceMessageService()
