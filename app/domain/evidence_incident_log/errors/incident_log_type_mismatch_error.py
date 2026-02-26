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
                            "message": "사건 일지 타입이 불일치한 작업을 시도했습니다.",
                            "debug_message": "ID: 123e4567-e89b-12d3-a456-426614174000에 해당하는 사건 일지 타입이 FILE가 아닙니다.",
                        },
                    }
                }
            }
        },
    },
}
