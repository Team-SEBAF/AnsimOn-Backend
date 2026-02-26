from enum import Enum

from botocore.exceptions import ClientError

from app.base.base_error import BaseErrorResponse, CodeException


class VerifyEmailErrorCode(str, Enum):
    """
    이메일 인증 에러 코드

    - INVALID_CODE: 인증 코드가 일치하지 않음
    - EXPIRED_CODE: 인증 코드가 만료됨
    """

    INVALID_CODE = "INVALID_CODE"
    EXPIRED_CODE = "EXPIRED_CODE"


class VerifyEmailErrorResponse(BaseErrorResponse):
    code: VerifyEmailErrorCode
    message: str


VERIFY_EMAIL_ERRORS_RESPONSES = {
    400: {
        "model": VerifyEmailErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "INVALID_CODE": {
                        "summary": "인증 코드가 일치하지 않습니다.",
                        "value": {
                            "code": "INVALID_CODE",
                            "message": "인증 코드가 일치하지 않습니다.",
                            "debug_message": "인증 코드가 일치하지 않습니다. code: CodeMismatchException",
                        },
                    }
                }
            }
        },
    },
    409: {
        "model": VerifyEmailErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "EXPIRED_CODE": {
                        "summary": "인증 코드가 만료되었습니다.",
                        "value": {
                            "code": "EXPIRED_CODE",
                            "message": "인증 코드가 만료되었습니다.",
                            "debug_message": "인증 코드가 만료되었습니다. code: ExpiredCodeException",
                        },
                    }
                }
            }
        },
    },
}


def handle_verify_email_error(e: ClientError):
    code = e.response["Error"]["Code"]

    if code == "CodeMismatchException":
        raise CodeException(
            code=VerifyEmailErrorCode.INVALID_CODE,
            message="인증 코드가 일치하지 않습니다.",
            debug_message=f"인증 코드가 일치하지 않습니다. code: {code}",
            status_code=400,
        )
    elif code == "ExpiredCodeException":
        raise CodeException(
            code=VerifyEmailErrorCode.EXPIRED_CODE,
            message="인증 코드가 만료되었습니다.",
            debug_message=f"인증 코드가 만료되었습니다. code: {code}",
            status_code=400,
        )
