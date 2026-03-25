from enum import Enum

from app.base.base_error import BaseErrorResponse


class SseUrlErrorCode(str, Enum):
    """SSE 서버 URL 조회 에러 코드"""

    SSE_NOT_CONFIGURED = "SSE_NOT_CONFIGURED"
    SSE_SERVER_NOT_RUNNING = "SSE_SERVER_NOT_RUNNING"
    SSE_PUBLIC_IP_UNAVAILABLE = "SSE_PUBLIC_IP_UNAVAILABLE"


class SseUrlErrorResponse(BaseErrorResponse):
    code: SseUrlErrorCode
    message: str


SSE_URL_ERRORS_RESPONSES = {
    503: {
        "model": SseUrlErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "SSE_NOT_CONFIGURED": {
                        "summary": "SSE ECS 설정 없음",
                        "value": {
                            "code": "SSE_NOT_CONFIGURED",
                            "message": "SSE ECS 클러스터·서비스가 설정되어 있지 않습니다.",
                            "debug_message": "환경 변수 SSE_ECS_CLUSTER, SSE_ECS_SERVICE를 설정하세요.",
                        },
                    },
                    "SSE_SERVER_NOT_RUNNING": {
                        "summary": "SSE 서버(태스크) 미실행",
                        "value": {
                            "code": "SSE_SERVER_NOT_RUNNING",
                            "message": "실행 중인 SSE 서버 태스크가 없습니다.",
                            "debug_message": "ECS 서비스에 RUNNING 태스크가 없습니다.",
                        },
                    },
                    "SSE_PUBLIC_IP_UNAVAILABLE": {
                        "summary": "Public IP 없음",
                        "value": {
                            "code": "SSE_PUBLIC_IP_UNAVAILABLE",
                            "message": "태스크에 Public IP를 조회할 수 없습니다.",
                            "debug_message": "네트워크 인터페이스에 PublicIp가 없습니다.",
                        },
                    },
                }
            }
        },
    },
}
