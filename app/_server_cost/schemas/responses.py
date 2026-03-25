from typing import Literal

from app.base.base_response import BaseResponse


class InfraStatusResponse(BaseResponse):
    """인프라(DB, SSE 등) 사용 가능 여부. available / unavailable 로 구분."""

    status: Literal["available", "unavailable"]
