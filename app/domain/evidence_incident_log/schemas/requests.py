from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest, create_partial_request
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence.schemas.common import EvidencePresignedUrlItemRequest
from app.domain.evidence_incident_log.schemas.dtos import EvidenceIncidentLogFormDataDTO


class EvidenceIncidentLogFileRegisterItemRequest(BaseRequest):
    incident_log_id: UUID = Field(..., description="Presigned URL 발급 시 받은 incident_log_id")
    filename: str = Field(..., description="파일명", examples=["evidence.pdf"])
    file_created_at: datetime = Field(..., description="원본 파일 생성 시각")


class EvidenceIncidentLogFileRegisterRequest(BaseRequest):
    items: list[EvidenceIncidentLogFileRegisterItemRequest] = Field(
        ...,
        min_length=1,
        max_length=EVIDENCE_DOCUMENT_RESTRICT.max_count,
        description="등록할 사건 일지 파일 목록",
    )


class EvidenceIncidentLogFormDataUploadRequest(BaseRequest, EvidenceIncidentLogFormDataDTO):
    pass


EvidenceIncidentLogFormDataUpdateRequest = create_partial_request(
    EvidenceIncidentLogFormDataDTO, "EvidenceIncidentLogFormDataUpdateRequest"
)


class FormDataAttachmentPresignedRequest(BaseRequest):
    items: list[EvidencePresignedUrlItemRequest] = Field(
        ...,
        min_length=1,
        description="첨부할 파일 목록",
    )


class FormDataAttachmentRegisterItemRequest(BaseRequest):
    attachment_id: UUID = Field(..., description="Presigned URL 발급 시 받은 attachment_id")
    filename: str = Field(..., description="파일명")


class FormDataAttachmentRegisterRequest(BaseRequest):
    items: list[FormDataAttachmentRegisterItemRequest] = Field(
        ...,
        min_length=1,
        description="등록할 첨부 자료 목록",
    )


class FormDataAttachmentDeleteRequest(BaseRequest):
    attachment_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="삭제할 첨부 자료 ID 목록",
    )
