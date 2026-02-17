from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.auth import AuthUser
from app.core.aws import download_s3_object, upload_fileobj
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence import EvidenceTypeService
from app.domain.evidence.constant import EVIDENCE_MESSAGE_RESTRICT, EvidenceVariant
from app.domain.evidence.errors.register_validation_error import (
    raise_evidence_register_validation_failed,
)
from app.domain.evidence.utils import (
    check_register_max_count,
    fetch_s3_metadata_for_register,
)
from app.domain.evidence_message import schemas

from .models.evidence_message_model import EvidenceMessage
from .repos.evidence_message_repository import EvidenceMessageRepository
from .utils import extract_image_meta, make_image_top_crop


def _validate_message_register_restrict(metadata_list: list[dict]) -> None:
    """content_type 먼저, 통과한 것만 size. duration 없음."""
    restrict = EVIDENCE_MESSAGE_RESTRICT
    content_type_failed_evidence_ids: list[str] = []
    size_bytes_failed_evidence_ids: list[str] = []

    for m in metadata_list:
        eid_str = str(m["message_id"])
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

    def register_message(
        self,
        complaint: Complaint,
        request: schemas.EvidenceMessageRegisterRequest,
        db: Session,
    ) -> schemas.EvidenceMessageRegisterListResponse:
        # 1) max_count 검사
        total_count = self._get_total_count(
            complaint_id=complaint.complaint_id,
            db=db,
        )
        check_register_max_count(
            total_count=total_count,
            request_count=len(request.items),
            restrict=EVIDENCE_MESSAGE_RESTRICT,
            type_name="MESSAGE",
        )
        # 2) S3 메타데이터 조회
        metadata_list = fetch_s3_metadata_for_register(
            complaint=complaint,
            items=request.items,
            path_segment="messages",
            get_evidence_id=lambda item: item.message_id,
            build_extra=lambda item, s3_key, ct, size: {
                "message_id": item.message_id,
                "complaint_id": complaint.complaint_id,
                "filename": item.filename,
            },
        )
        # 3) content_type, size 검증
        _validate_message_register_restrict(metadata_list)

        # 4) 다운로드 → 이미지 추출 → 썸네일/디테일 S3 업로드 (병렬)
        def _process_message_item(m: dict) -> dict:
            file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
            width, height, _ = extract_image_meta(file_bytes)
            base_key = m["s3_key"].rsplit("/", 1)[0]
            thumbnail_key = f"{base_key}/thumbnail"
            detail_key = f"{base_key}/detail"
            thumbnail_bytes, _, _ = make_image_top_crop(file_bytes=file_bytes, size=120, quality=65)
            detail_bytes, _, _ = make_image_top_crop(file_bytes=file_bytes, size=400, quality=75)
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
            return {
                "message_id": m["message_id"],
                "complaint_id": m["complaint_id"],
                "filename": m["filename"],
                "s3_key": m["s3_key"],
                "content_type": m["content_type"],
                "size_bytes": m["size_bytes"],
                "width": width,
                "height": height,
            }

        with ThreadPoolExecutor(max_workers=max(1, min(len(metadata_list), 5))) as executor:
            rows = list(executor.map(_process_message_item, metadata_list))
        # 5) DB 저장
        db.bulk_insert_mappings(EvidenceMessage, rows)
        db.commit()

        results = [
            schemas.EvidenceMessageRegisterItemResponse(
                message_id=r["message_id"],
                filename=r["filename"],
                content_type=r["content_type"],
                width=r["width"],
                height=r["height"],
                size_bytes=r["size_bytes"],
            )
            for r in rows
        ]
        return schemas.EvidenceMessageRegisterListResponse(items=results)

    def get_preview_messages(
        self,
        complaint: Complaint,
        limit: int,
        db: Session,
    ) -> schemas.EvidenceMessagePreviewListResponse:
        messages, total_count = self._get_limit_messages_and_total_count(
            complaint=complaint,
            limit=limit,
            db=db,
        )

        previews: list[schemas.EvidenceMessagePreviewResponse] = []
        for message in messages:
            s3_key_base = message.s3_key.rsplit("/", 1)[0]
            url = super()._get_presigned_url(
                s3_key=f"{s3_key_base}/{EvidenceVariant.THUMBNAIL.value}",
                expires_in=60 * 60,  # 1시간
            )
            previews.append(
                schemas.EvidenceMessagePreviewResponse(
                    message_id=message.message_id,
                    thumbnail_url=url,
                )
            )

        return schemas.EvidenceMessagePreviewListResponse(
            previews=previews,
            total_count=total_count,
        )

    def get_detail_messages(
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
                    thumbnail_url=url,
                )
            )
        return schemas.EvidenceMessageDetailListResponse(
            details=details,
            total_count=total_count,
        )

    def get_original_message(
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
            created_at=message.created_at,
            updated_at=message.updated_at,
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
