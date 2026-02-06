from enum import Enum

from app.base.base_error import BaseErrorResponse


class GetEvidenceErrorCode(str, Enum):
    """
    증거 조회 에러 코드

    - EVIDENCE_NOT_FOUND: 증거를 찾을 수 없음
    - NO_PERMISSION: 증거 접근 권한이 없음
    """

    EVIDENCE_NOT_FOUND = "EVIDENCE_NOT_FOUND"
    NO_PERMISSION = "NO_PERMISSION"


class GetEvidenceErrorResponse(BaseErrorResponse):
    code: GetEvidenceErrorCode
    message: str


GET_EVIDENCE_ERRORS_RESPONSES = {
    404: {
        "model": GetEvidenceErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "EVIDENCE_NOT_FOUND": {
                        "summary": "증거를 찾을 수 없습니다.",
                        "value": {
                            "code": "EVIDENCE_NOT_FOUND",
                            "message": "증거를 찾을 수 없습니다.",
                        },
                    }
                }
            }
        },
    },
    403: {
        "model": GetEvidenceErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "NO_PERMISSION": {
                        "summary": "증거 접근 권한이 없습니다.",
                        "value": {
                            "code": "NO_PERMISSION",
                            "message": "증거 접근 권한이 없습니다.",
                        },
                    }
                }
            }
        },
    },
}
