from enum import Enum

from app.base.base_error import BaseErrorResponse


class GetComplaintErrorCode(str, Enum):
    """
    고소장 조회 에러 코드

    - COMPLAINT_NOT_FOUND: 고소장을 찾을 수 없음
    - NO_PERMISSION: 고소장 접근 권한이 없음
    """

    COMPLAINT_NOT_FOUND = "COMPLAINT_NOT_FOUND"
    NO_PERMISSION = "NO_PERMISSION"


class GetComplaintErrorResponse(BaseErrorResponse):
    code: GetComplaintErrorCode
    message: str


GET_COMPLAINT_ERRORS_RESPONSES = {
    404: {
        "model": GetComplaintErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "COMPLAINT_NOT_FOUND": {
                        "summary": "고소장을 찾을 수 없습니다.",
                        "value": {
                            "code": "COMPLAINT_NOT_FOUND",
                            "message": "고소장을 찾을 수 없습니다.",
                            "debug_message": "complaint_id: 123e4567-e89b-12d3-a456-426614174000에 해당하는 고소장을 찾을 수 없습니다.",
                        },
                    }
                }
            }
        },
    },
    403: {
        "model": GetComplaintErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "NO_PERMISSION": {
                        "summary": "고소장 접근 권한이 없습니다.",
                        "value": {
                            "code": "NO_PERMISSION",
                            "message": "해당 고소장 스페이스에 대한 접근 권한이 없습니다.",
                            "debug_message": "complaint_id: 123e4567-e89b-12d3-a456-426614174000에 해당하는 고소장 접근 권한이 없습니다.",
                        },
                    }
                }
            }
        },
    },
}
