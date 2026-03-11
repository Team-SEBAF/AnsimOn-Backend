from enum import Enum

from app.base.base_error import BaseErrorResponse


class GetTimelineErrorCode(str, Enum):
    TIMELINE_NOT_FOUND = "TIMELINE_NOT_FOUND"


class GetTimelineErrorResponse(BaseErrorResponse):
    code: GetTimelineErrorCode
    message: str


GET_TIMELINE_ERRORS_RESPONSES = {
    404: {
        "model": GetTimelineErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "TIMELINE_NOT_FOUND": {
                        "summary": "타임라인을 찾을 수 없습니다.",
                        "value": {
                            "code": "TIMELINE_NOT_FOUND",
                            "message": "타임라인을 찾을 수 없습니다.",
                            "debug_message": "complaint_id에 해당하는 타임라인이 없습니다.",
                        },
                    }
                }
            }
        },
    },
}
