from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest
from app.domain.evidence.constant import EVIDENCE_TRACKING_RESTRICT


class EvidenceTrackingRegisterItemRequest(BaseRequest):
    tracking_id: UUID = Field(..., description="Presigned URL 발급 시 받은 tracking_id")
    filename: str = Field(..., description="파일명", examples=["evidence.mp4"])


class EvidenceTrackingRegisterRequest(BaseRequest):
    items: list[EvidenceTrackingRegisterItemRequest] = Field(
        ...,
        min_length=1,
        max_length=EVIDENCE_TRACKING_RESTRICT.max_count,
        description="등록할 증거 추적 목록",
    )
