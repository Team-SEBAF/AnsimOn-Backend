from enum import Enum
from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest


class EvidenceType(str, Enum):
    """증거 타입

    MESSAGE: 메신저, 문자, DM
    VOICE: 통화, 음성
    TRACKING: 접근, 추적 흔적
    INCIDENT_LOG: 신고, 상담 기록
    REPORT_RECORD: 사건 일지
    """

    MESSAGE = "MESSAGE"
    VOICE = "VOICE"
    TRACKING = "TRACKING"
    REPORT_RECORD = "REPORT_RECORD"
    INCIDENT_LOG = "INCIDENT_LOG"


class UpdateEvidenceFilenameRequest(BaseRequest):
    type: EvidenceType = Field(
        ...,
        description="증거 타입",
        examples=[EvidenceType.MESSAGE],
    )
    filename: str = Field(..., description="새 파일명", examples=["증거_이미지"])


class DeleteEvidenceRequest(BaseRequest):
    type: EvidenceType = Field(
        ...,
        description="증거 타입 (한 요청당 한 타입만)",
        examples=[EvidenceType.MESSAGE],
    )
    evidence_ids: list[UUID] = Field(
        ...,
        description="삭제할 증거 ID 목록 (해당 타입의 ID, 예: message_id, voice_id)",
        min_length=1,
        examples=[[UUID("123e4567-e89b-12d3-a456-426614174000")]],
    )
