from enum import Enum

from pydantic import Field

from app.base.base_request import BaseRequest


class EvidenceType(str, Enum):
    """증거 타입

    MESSAGE: 메신저, 문자, DM
    AUDIO: 통화, 음성
    TRACKING: 접근, 추적 흔적
    INCIDENT_LOG: 신고, 상담 기록
    REPORT_RECORD: 사건 일지
    """

    MESSAGE = "MESSAGE"
    AUDIO = "AUDIO"
    TRACKING = "TRACKING"
    INCIDENT_LOG = "INCIDENT_LOG"
    REPORT_RECORD = "REPORT_RECORD"


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
        description="증거 타입",
        examples=[EvidenceType.MESSAGE],
    )
