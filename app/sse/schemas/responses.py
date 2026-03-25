from pydantic import Field

from app.base.base_response import BaseResponse


class SseServerUrlResponse(BaseResponse):
    """프론트에서 SSE API 호출 시 prefix로 사용할 베이스 URL."""

    base_url: str = Field(
        ...,
        description="SSE 서버 베이스 URL (예: http://1.2.3.4:8000)",
        examples=["http://15.164.95.247:8000"],
    )
