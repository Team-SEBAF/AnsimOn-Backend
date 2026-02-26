from enum import Enum

from botocore.exceptions import ClientError

from app.base.base_error import BaseErrorResponse, CodeException


class RefreshTokenErrorCode(str, Enum):
    """
    리프레시 토큰 에러 코드

    - INVALID_REFRESH_TOKEN: 리프레시 토큰이 유효하지 않거나 만료되었음
    """

    INVALID_REFRESH_TOKEN = "INVALID_REFRESH_TOKEN"


class RefreshTokenErrorResponse(BaseErrorResponse):
    code: RefreshTokenErrorCode
    message: str


REFRESH_TOKEN_ERRORS_RESPONSES = {
    401: {
        "model": RefreshTokenErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "INVALID_REFRESH_TOKEN": {
                        "summary": "리프레시 토큰이 유효하지 않거나 만료되었음",
                        "value": {
                            "code": "INVALID_REFRESH_TOKEN",
                            "message": "리프레시 토큰이 유효하지 않거나 만료되었습니다. 다시 로그인해 주세요.",
                            "debug_message": "리프레시 토큰이 유효하지 않거나 만료되었습니다. code: NotAuthorizedException",
                        },
                    }
                }
            }
        },
    },
}


def handle_refresh_token_error(e: ClientError):
    code = e.response["Error"]["Code"]

    if code == "NotAuthorizedException":
        raise CodeException(
            code=RefreshTokenErrorCode.INVALID_REFRESH_TOKEN,
            message="리프레시 토큰이 유효하지 않거나 만료되었습니다. 다시 로그인해 주세요.",
            debug_message=f"리프레시 토큰이 유효하지 않거나 만료되었습니다. code: {code}",
            status_code=401,
        )
