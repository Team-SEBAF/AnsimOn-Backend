from enum import Enum

from app.base.base_error import BaseErrorResponse


class GetEvidenceMessageErrorCode(str, Enum):
    """
    증거 메시지 조회 에러 코드

    - EVIDENCE_MESSAGE_NOT_FOUND: 증거 메시지를 찾을 수 없음
    - NO_PERMISSION: 증거 메시지 접근 권한이 없음
    """

    EVIDENCE_MESSAGE_NOT_FOUND = "EVIDENCE_MESSAGE_NOT_FOUND"
    NO_PERMISSION = "NO_PERMISSION"


class GetEvidenceMessageErrorResponse(BaseErrorResponse):
    code: GetEvidenceMessageErrorCode
    message: str


GET_EVIDENCE_MESSAGE_ERRORS_RESPONSES = {
    404: {
        "model": GetEvidenceMessageErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "EVIDENCE_MESSAGE_NOT_FOUND": {
                        "summary": "증거 메시지를 찾을 수 없습니다.",
                        "value": {
                            "code": "EVIDENCE_MESSAGE_NOT_FOUND",
                            "message": "증거 메시지를 찾을 수 없습니다.",
                        },
                    }
                }
            }
        },
    },
    403: {
        "model": GetEvidenceMessageErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "NO_PERMISSION": {
                        "summary": "증거 메시지 접근 권한이 없습니다.",
                        "value": {
                            "code": "NO_PERMISSION",
                            "message": "증거 메시지 접근 권한이 없습니다.",
                        },
                    }
                }
            }
        },
    },
}
