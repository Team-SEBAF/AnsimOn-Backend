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
from .utils import extract_image_meta


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

        for file in files:
            file_bytes = file.file.read()

            # 1. 이미지 메타데이터
            width, height = extract_image_meta(file_bytes)
            file.file.seek(0)  # 파일 포인터를 처음으로 되돌림

            # 2. ID 생성
            message_id = uuid4()

            # 3. S3 key
            s3_key = f"{complaint.user_sub}/complaints/{complaint.complaint_id}/evidences/messages/{message_id}/original"

            # 4. S3 업로드
            upload_fileobj(
                fileobj=file.file,
                bucket=settings.S3_BUCKET_NAME,
                key=s3_key,
                content_type=file.content_type,
            )

            # 5. DB 객체 생성
            message = EvidenceMessage(
                id=message_id,
                complaint_id=complaint.complaint_id,
                filename=file.filename,
                s3_key=s3_key,
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
                    id=m.id,
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
            ExpiresIn=60 * 60,  # 1시간
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
