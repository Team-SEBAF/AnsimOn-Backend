from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser
from app.core.aws import get_s3_client, upload_fileobj
from app.core.settings import settings
from app.domain.complaint import Complaint, ComplaintRepository
from app.domain.evidence.message import schemas

from .errors.get_message_error import GetEvidenceMessageErrorCode
from .models.evidence_message_model import EvidenceMessage
from .repos.evidence_message_repository import EvidenceMessageRepository
from .utils import extract_image_meta, make_image_top_crop


class EvidenceMessageService:
    def check_access_permission(
        self, message: EvidenceMessage, current_user: AuthUser, db: Session
    ) -> None:
        complaint_repo = ComplaintRepository(db)
        complaint = complaint_repo.get(message.complaint_id)

        if complaint.user_sub != current_user.user_sub:
            raise CodeException(
                code=GetEvidenceMessageErrorCode.NO_PERMISSION,
                message=f"message_id: {message.message_id}에 해당하는 증거 메시지 접근 권한이 없습니다.",
                status_code=403,
            )

    def upload_images(
        self,
        complaint: Complaint,
        files: list[UploadFile],
        db: Session,
    ) -> schemas.EvidenceMessageUploadResponse:
        evidence_message_repo = EvidenceMessageRepository(db)
        results: list[EvidenceMessage] = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            for file in files:
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

                original_key = f"{base_key}/original.jpg"
                thumbnail_key = f"{base_key}/thumbnail.jpg"
                middle_key = f"{base_key}/middle.jpg"

                # 파생 이미지 생성
                thumbnail_bytes, _, _ = make_image_top_crop(
                    file_bytes=file_bytes,
                    size=160,
                    quality=65,
                )

                middle_bytes, _, _ = make_image_top_crop(
                    file_bytes=file_bytes,
                    size=512,
                    quality=80,
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
                        fileobj=BytesIO(middle_bytes),
                        bucket=settings.S3_BUCKET_NAME,
                        key=middle_key,
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
            ]
        )

    def get_original_image(
        self,
        message_id: UUID,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.EvidenceMessageOriginalImageResponse:
        message_repo = EvidenceMessageRepository(db)

        message = message_repo.get(message_id)
        if not message:
            raise CodeException(
                code=GetEvidenceMessageErrorCode.EVIDENCE_MESSAGE_NOT_FOUND,
                message=f"message_id: {message_id}에 해당하는 증거 메시지를 찾을 수 없습니다.",
                status_code=404,
            )

        self.check_access_permission(message, current_user, db)

        # presigned URL 생성
        s3 = get_s3_client()
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": message.s3_key,
            },
            ExpiresIn=60 * 10,  # 10분
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


evidence_message_service = EvidenceMessageService()
