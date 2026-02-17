from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest, create_partial_request
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT
from app.domain.evidence_incident_log.schemas.dtos import EvidenceIncidentLogFormDataDTO


class EvidenceIncidentLogFileRegisterItemRequest(BaseRequest):
    incident_log_id: UUID = Field(..., description="Presigned URL 발급 시 받은 incident_log_id")
    filename: str = Field(..., description="파일명", examples=["evidence.pdf"])


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
