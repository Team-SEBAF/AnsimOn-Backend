from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest
from app.domain.evidence.constant import EVIDENCE_VICTIM_RESTRICT


class EvidenceVictimRegisterItemRequest(BaseRequest):
    victim_id: UUID = Field(..., description="Presigned URL 발급 시 받은 victim_id")
    filename: str = Field(..., description="파일명", examples=["evidence.mp4"])
    file_created_at: datetime = Field(..., description="원본 파일 생성 시각")


class EvidenceVictimRegisterRequest(BaseRequest):
    items: list[EvidenceVictimRegisterItemRequest] = Field(
        ...,
        min_length=1,
        max_length=EVIDENCE_VICTIM_RESTRICT.max_count,
        description="등록할 피해 사진/영상 목록",
    )
