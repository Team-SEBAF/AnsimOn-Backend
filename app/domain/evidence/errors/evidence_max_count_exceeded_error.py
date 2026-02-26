from enum import Enum

from app.base.base_error import BaseErrorResponse


class EvidenceMaxCountExceededErrorCode(str, Enum):
    """
    증거 업로드 최대 개수 초과 에러 코드

    - EVIDENCE_MAX_COUNT_EXCEEDED: 증거 최대 개수를 초과했음
    """

    EVIDENCE_MAX_COUNT_EXCEEDED = "EVIDENCE_MAX_COUNT_EXCEEDED"


class EvidenceMaxCountExceededErrorResponse(BaseErrorResponse):
    code: EvidenceMaxCountExceededErrorCode
    message: str


EVIDENCE_MAX_COUNT_EXCEEDED_ERRORS_RESPONSES = {
    400: {
        "model": EvidenceMaxCountExceededErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "EVIDENCE_MAX_COUNT_EXCEEDED": {
                        "summary": "증거 최대 개수를 초과했습니다.",
                        "value": {
                            "code": "EVIDENCE_MAX_COUNT_EXCEEDED",
                            "message": "해당 증거 타입의 최대 개수를 초과했습니다.",
                            "debug_message": "MESSAGE 타입 증거의 최대 개수(10개)를 초과합니다. (현재 8개 + 요청 5개)",
                        },
                    }
                }
            }
        },
    },
}
