from botocore.exceptions import ClientError

from app.base import BaseException


class SignUpException(BaseException):
    def __init__(self, code: str, message: str, status_code: int):
        super().__init__(message, status_code)
        self.code = code


def handle_cognito_signup_error(e: ClientError):
    code = e.response["Error"]["Code"]

    if code == "UsernameExistsException":
        raise SignUpException(
            code="EMAIL_ALREADY_EXISTS",
            message="이미 가입된 이메일입니다.",
            status_code=409,
        )

    if code == "InvalidPasswordException":
        raise SignUpException(
            code="INVALID_PASSWORD",
            message="비밀번호가 정책을 만족하지 않습니다.",
            status_code=400,
        )

    if code == "InvalidParameterException":
        raise SignUpException(
            code="INVALID_REQUEST",
            message="잘못된 요청입니다.",
            status_code=400,
        )

    if code == "TooManyRequestsException":
        raise SignUpException(
            code="TOO_MANY_REQUESTS",
            message="요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
            status_code=429,
        )

    # 나머지는 서버 에러
    raise SignUpException(
        code="INTERNAL_SERVER_ERROR",
        message="회원가입 처리 중 오류가 발생했습니다.",
        status_code=500,
    )
