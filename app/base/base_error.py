from enum import Enum

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class BaseErrorResponse(BaseModel):
    code: str = Field(
        ...,
        description="에러 코드 (프론트 분기용)",
        examples=["INVALID_REQUEST"],
    )
    message: str = Field(
        ...,
        description="에러 메시지 (사람이 읽는 용도)",
        examples=["잘못된 요청입니다."],
    )


class CodeException(Exception):
    def __init__(self, *, code: Enum, message: str, status_code: int):
        super().__init__(message)  # instance.args[0]으로 접근 가능
        self.status_code = status_code
        self.code = code  # Enum
        self.message = message


def register_exception_handlers(app):
    # Validation Error (422)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=BaseErrorResponse(
                code="VALIDATION_ERROR",
                message="요청 값이 올바르지 않습니다.",
            ).model_dump(),
        )

    # HTTPException (401, 403, 404 등)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=BaseErrorResponse(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
            ).model_dump(),
        )

    # 도메인 에러
    @app.exception_handler(CodeException)
    async def code_exception_handler(request: Request, exc: CodeException):
        return JSONResponse(
            status_code=exc.status_code,
            content=BaseErrorResponse(
                code=exc.code.value,
                message=exc.message,
            ).model_dump(),
        )

    # 처리되지 않은 에러
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=BaseErrorResponse(
                code="INTERNAL_SERVER_ERROR",
                message="서버 오류가 발생했습니다.",
            ).model_dump(),
        )
