from typing import Literal

from app.base.base_response import BaseResponse


class InfraStatusResponse(BaseResponse):
    status: Literal["available", "unavailable"]
