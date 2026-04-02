from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest
from app.domain.evidence.constant import EVIDENCE_VOICE_RESTRICT


class EvidenceVoiceRegisterItemRequest(BaseRequest):
    voice_id: UUID = Field(..., description="Presigned URL 발급 시 받은 voice_id")
    filename: str = Field(..., description="파일명", examples=["evidence.mp3"])
    file_created_at: datetime = Field(..., description="원본 파일 생성 시각")


class EvidenceVoiceRegisterRequest(BaseRequest):
    items: list[EvidenceVoiceRegisterItemRequest] = Field(
        ...,
        min_length=1,
        max_length=EVIDENCE_VOICE_RESTRICT.max_count,
        description="등록할 증거 음성 목록",
    )
