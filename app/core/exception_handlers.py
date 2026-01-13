from fastapi import Request
from fastapi.responses import JSONResponse

from app.base import BaseException, CodeException


def register_exception_handlers(app):
    """FastAPI 앱에 예외 핸들러를 등록합니다."""

    @app.exception_handler(BaseException)
    async def base_exception_handler(request: Request, exc: BaseException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.message,
            },
        )

    @app.exception_handler(CodeException)
    async def code_exception_handler(request: Request, exc: CodeException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
            },
        )
