from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.aws import upload_fileobj
from app.core.settings import settings
from app.domain.complaint import Complaint

from .models.evidence_message_model import EvidenceMessage
from .repos.evidence_message_repository import EvidenceMessageRepository
from .schemas import (
    EvidenceMessageResponse,
    EvidenceMessageUploadResponse,
)
from .utils import extract_image_meta


class EvidenceMessageService:
    def upload_images(
        self,
        complaint: Complaint,
        files: list[UploadFile],
        db: Session,
    ) -> EvidenceMessageUploadResponse:
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

        return EvidenceMessageUploadResponse(
            images=[
                EvidenceMessageResponse(
                    id=m.id,
                    filename=m.filename,
                    width=m.width,
                    height=m.height,
                    size_bytes=m.size_bytes,
                )
                for m in results
            ]
        )


evidence_message_service = EvidenceMessageService()
