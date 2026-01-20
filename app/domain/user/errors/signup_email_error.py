from enum import Enum

from botocore.exceptions import ClientError

from app.base import CodeException
from app.base.base_error import BaseErrorResponse


class SignupErrorCode(str, Enum):
    """
    회원가입 에러 코드

    - EMAIL_ALREADY_EXISTS: 이미 가입된 이메일
    - INVALID_PASSWORD: 비밀번호 정책 위반
    """

    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    INVALID_PASSWORD = "INVALID_PASSWORD"


class SignUpErrorResponse(BaseErrorResponse):
    code: SignupErrorCode
    message: str


SIGNUP_EMAIL_ERRORS_RESPONSES = {
    400: {
        "model": SignUpErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "INVALID_PASSWORD": {
                        "summary": "비밀번호 정책 위반",
                        "value": {
                            "code": "INVALID_PASSWORD",
                            "message": "비밀번호가 정책을 만족하지 않습니다.",
                        },
                    }
                }
            }
        },
    },
    409: {
        "model": SignUpErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "EMAIL_ALREADY_EXISTS": {
                        "summary": "이미 가입된 이메일",
                        "value": {
                            "code": "EMAIL_ALREADY_EXISTS",
                            "message": "이미 가입된 이메일입니다.",
                        },
                    }
                }
            }
        },
    },
}


def handle_signup_email_error(e: ClientError):
    code = e.response["Error"]["Code"]

    if code == "UsernameExistsException":
        raise CodeException(
            code=SignupErrorCode.EMAIL_ALREADY_EXISTS,
            message="이미 가입된 이메일입니다.",
            status_code=409,
        )
    elif code == "InvalidPasswordException":
        raise CodeException(
            code=SignupErrorCode.INVALID_PASSWORD,
            message="비밀번호가 정책을 만족하지 않습니다.",
            status_code=400,
        )
