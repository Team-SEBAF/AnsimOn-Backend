from enum import Enum

from botocore.exceptions import ClientError

from app.base.base_error import BaseErrorResponse, CodeException


class LoginEmailErrorCode(str, Enum):
    """
    이메일 로그인 에러 코드

    - INVALID_CREDENTIALS: 잘못된 이메일 또는 비밀번호 (Cognito InitiateAuth는 미가입/오비번 구분 없이 NotAuthorizedException)
    - USER_NOT_CONFIRMED: 이메일 인증이 완료되지 않음
    """

    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    USER_NOT_CONFIRMED = "USER_NOT_CONFIRMED"


class LoginEmailErrorResponse(BaseErrorResponse):
    code: LoginEmailErrorCode
    message: str


LOGIN_EMAIL_ERRORS_RESPONSES = {
    401: {
        "model": LoginEmailErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "INVALID_CREDENTIALS": {
                        "summary": "잘못된 이메일 또는 비밀번호",
                        "value": {
                            "code": "INVALID_CREDENTIALS",
                            "message": "잘못된 이메일 또는 비밀번호입니다.",
                            "debug_message": "잘못된 이메일 또는 비밀번호입니다. code: NotAuthorizedException",
                        },
                    }
                }
            }
        },
    },
    403: {
        "model": LoginEmailErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "USER_NOT_CONFIRMED": {
                        "summary": "이메일 인증이 완료되지 않음",
                        "value": {
                            "code": "USER_NOT_CONFIRMED",
                            "message": "이메일 인증이 완료되지 않았습니다. 이메일 인증을 완료한 후 다시 시도해 주세요.",
                            "debug_message": "이메일 인증이 완료되지 않았습니다. code: UserNotConfirmedException",
                        },
                    }
                }
            }
        },
    },
}


def handle_login_email_error(e: ClientError):
    code = e.response["Error"]["Code"]

    if code == "NotAuthorizedException":
        raise CodeException(
            code=LoginEmailErrorCode.INVALID_CREDENTIALS,
            message="잘못된 이메일 또는 비밀번호입니다.",
            debug_message=f"잘못된 이메일 또는 비밀번호입니다. code: {code}",
            status_code=401,
        )
    if code == "UserNotConfirmedException":
        raise CodeException(
            code=LoginEmailErrorCode.USER_NOT_CONFIRMED,
            message="이메일 인증이 완료되지 않았습니다. 이메일 인증을 완료한 후 다시 시도해 주세요.",
            debug_message=f"이메일 인증이 완료되지 않았습니다. code: {code}",
            status_code=403,
        )
    raise e
