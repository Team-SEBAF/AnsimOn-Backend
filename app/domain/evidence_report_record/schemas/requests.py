from uuid import UUID

from pydantic import Field

from app.base.base_request import BaseRequest
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT


class EvidenceReportRecordRegisterItemRequest(BaseRequest):
    report_record_id: UUID = Field(..., description="Presigned URL 발급 시 받은 report_record_id")
    filename: str = Field(..., description="파일명", examples=["evidence.pdf"])


class EvidenceReportRecordRegisterRequest(BaseRequest):
    items: list[EvidenceReportRecordRegisterItemRequest] = Field(
        ...,
        min_length=1,
        max_length=EVIDENCE_DOCUMENT_RESTRICT.max_count,
        description="등록할 신고・사건 일지 목록",
    )
