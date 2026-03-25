from enum import Enum

from app.base.base_error import BaseErrorResponse


class CurrentTaskErrorCode(str, Enum):
    """
    현재 태스크 조회 에러 코드

    - NOT_TIMELINE_GENERATING: 타임라인 생성 중이 아닐 때 조회 시도
    """

    NOT_TIMELINE_GENERATING = "NOT_TIMELINE_GENERATING"


class CurrentTaskErrorResponse(BaseErrorResponse):
    code: CurrentTaskErrorCode
    message: str


CURRENT_TASK_ERRORS_RESPONSES = {
    400: {
        "model": CurrentTaskErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "NOT_TIMELINE_GENERATING": {
                        "summary": "타임라인 생성 중이 아닐 때 조회할 수 없습니다.",
                        "value": {
                            "code": "NOT_TIMELINE_GENERATING",
                            "message": "타임라인 생성 중이 아닐 때는 현재 태스크 ID를 조회할 수 없습니다.",
                            "debug_message": "complaint의 step이 TIMELINE_GENERATING이 아닙니다.",
                        },
                    },
                }
            }
        },
    },
}
