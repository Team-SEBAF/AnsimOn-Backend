from enum import Enum

from app.base.base_error import BaseErrorResponse


class IncidentLogTypeMismatchErrorCode(str, Enum):
    """
    사건 일지 타입 불일치 에러 코드

    - INCIDENT_LOG_TYPE_MISMATCH: 사건 일지 타입이 불일치함
    """

    INCIDENT_LOG_TYPE_MISMATCH = "INCIDENT_LOG_TYPE_MISMATCH"


class IncidentLogTypeMismatchErrorResponse(BaseErrorResponse):
    code: IncidentLogTypeMismatchErrorCode
    message: str


INCIDENT_LOG_TYPE_MISMATCH_ERRORS_RESPONSES = {
    400: {
        "model": IncidentLogTypeMismatchErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "INCIDENT_LOG_TYPE_MISMATCH": {
                        "summary": "사건 일지 타입이 불일치합니다.",
                        "value": {
                            "code": "INCIDENT_LOG_TYPE_MISMATCH",
                            "message": "FILE 타입이 아닙니다.",
                        },
                    }
                }
            }
        },
    },
}
