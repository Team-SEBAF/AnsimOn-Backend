from enum import Enum

from app.base.base_error import BaseErrorResponse


class CurrentTaskErrorCode(str, Enum):
    """
    현재 태스크 조회 에러 코드

    - NOT_GENERATING: 해당 AI 생성 단계(step)가 아닐 때 조회 시도
    """

    NOT_GENERATING = "NOT_GENERATING"


class CurrentTaskErrorResponse(BaseErrorResponse):
    code: CurrentTaskErrorCode
    message: str


CURRENT_TASK_ERRORS_RESPONSES = {
    400: {
        "model": CurrentTaskErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "NOT_GENERATING": {
                        "summary": "해당 생성 중이 아닐 때 조회할 수 없습니다.",
                        "value": {
                            "code": "NOT_GENERATING",
                            "message": "AI 생성 중이 아닐 때는 현재 태스크 ID를 조회할 수 없습니다.",
                            "debug_message": "complaint.step이 GENERATING이 아닙니다.",
                        },
                    },
                }
            }
        },
    },
}
