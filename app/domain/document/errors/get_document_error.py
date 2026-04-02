from enum import Enum

from app.base.base_error import BaseErrorResponse


class GetDocumentErrorCode(str, Enum):
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"


class GetDocumentErrorResponse(BaseErrorResponse):
    code: GetDocumentErrorCode
    message: str


GET_DOCUMENT_ERRORS_RESPONSES = {
    404: {
        "model": GetDocumentErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "DOCUMENT_NOT_FOUND": {
                        "summary": "문서를 찾을 수 없습니다.",
                        "value": {
                            "code": "DOCUMENT_NOT_FOUND",
                            "message": "문서를 찾을 수 없습니다.",
                            "debug_message": "complaint_id에 해당하는 문서가 없습니다.",
                        },
                    }
                }
            }
        },
    },
}
