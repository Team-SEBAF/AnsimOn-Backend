from enum import Enum

from app.base.base_error import BaseErrorResponse


class TimelineManualEvidenceNotAllowedErrorCode(str, Enum):
    """
    타임라인 직접 추가 증거 허용 불가 에러 코드

    - TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED: 해당 타임라인 증거는 AI 분석 증거(is_ai_original=True)라
      직접 추가 증거 API(Presigned URL, Register)를 사용할 수 없음.
    """

    TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED = "TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED"


class TimelineManualEvidenceNotAllowedErrorResponse(BaseErrorResponse):
    code: TimelineManualEvidenceNotAllowedErrorCode
    message: str


TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED_ERRORS_RESPONSES = {
    400: {
        "model": TimelineManualEvidenceNotAllowedErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED": {
                        "summary": "타임라인 증거 타입이 불일치한 작업을 시도했습니다.",
                        "value": {
                            "code": "TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED",
                            "message": "타임라인 증거 타입이 불일치한 작업을 시도했습니다.",
                            "debug_message": "timeline_evidence_id에 해당하는 증거가 AI 분석 증거(is_ai_original=True)입니다. 직접 추가 증거에만 사용 가능합니다.",
                        },
                    }
                }
            }
        },
    },
}
