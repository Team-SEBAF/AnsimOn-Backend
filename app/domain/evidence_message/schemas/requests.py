from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest
from app.domain.evidence.constant import EVIDENCE_MESSAGE_RESTRICT


class EvidenceMessageRegisterItemRequest(BaseRequest):
    message_id: UUID = Field(..., description="Presigned URL 발급 시 받은 message_id")
    filename: str = Field(..., description="파일명", examples=["evidence.jpg"])
    file_created_at: datetime = Field(..., description="원본 파일 생성 시각")


class EvidenceMessageRegisterRequest(BaseRequest):
    items: list[EvidenceMessageRegisterItemRequest] = Field(
        ...,
        min_length=1,
        max_length=EVIDENCE_MESSAGE_RESTRICT.max_count,
        description="등록할 증거 메시지 목록",
    )
