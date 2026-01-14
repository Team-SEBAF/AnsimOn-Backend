from botocore.exceptions import ClientError

from app.base import CodeException, InternalServerErrorException


def handle_cognito_signup_error(e: ClientError):
    code = e.response["Error"]["Code"]

    if code == "UsernameExistsException":
        raise CodeException(
            code="EMAIL_ALREADY_EXISTS",
            message="이미 가입된 이메일입니다.",
            status_code=409,
        )

    if code == "InvalidPasswordException":
        raise CodeException(
            code="INVALID_PASSWORD",
            message="비밀번호가 정책을 만족하지 않습니다.",
            status_code=400,
        )

    if code == "InvalidParameterException":
        raise CodeException(
            code="INVALID_REQUEST",
            message="잘못된 요청입니다.",
            status_code=400,
        )

    if code == "TooManyRequestsException":
        raise CodeException(
            code="TOO_MANY_REQUESTS",
            message="요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
            status_code=429,
        )

    # 나머지는 서버 에러
    raise InternalServerErrorException(
        message="회원가입 처리 중 서버 에러가 발생했습니다.",
    )


def handle_cognito_verify_email_error(e: ClientError):
    code = e.response["Error"]["Code"]

    if code == "CodeMismatchException":
        raise CodeException(
            code="INVALID_CODE",
            message="인증 코드가 일치하지 않습니다.",
            status_code=400,
        )

    if code == "ExpiredCodeException":
        raise CodeException(
            code="EXPIRED_CODE",
            message="인증 코드가 만료되었습니다.",
            status_code=400,
        )

    # 나머지는 서버 에러
    raise InternalServerErrorException(
        message="인증 처리 중 서버 에러가 발생했습니다.",
    )


def handle_cognito_login_email_error(e: ClientError):
    code = e.response["Error"]["Code"]

    if code == "UserNotFoundException":
        raise CodeException(
            code="USER_NOT_FOUND",
            message="사용자를 찾을 수 없습니다.",
            status_code=404,
        )

    if code == "NotAuthorizedException":
        raise CodeException(
            code="INVALID_CREDENTIALS",
            message="잘못된 이메일 또는 비밀번호입니다.",
            status_code=401,
        )

    # 나머지는 서버 에러
    raise InternalServerErrorException(
        message="이메일 로그인 처리 중 서버 에러가 발생했습니다.",
    )


def handle_cognito_refresh_token_error(e: ClientError):
    code = e.response["Error"]["Code"]
    print(e.response["Error"]["Message"])

    if code == "NotAuthorizedException":
        raise CodeException(
            code="INVALID_REFRESH_TOKEN",
            message="리프레시 토큰이 유효하지 않거나 만료되었습니다. 다시 로그인해 주세요.",
            status_code=401,
        )

    # 나머지는 서버 에러
    raise InternalServerErrorException(
        message="리프레시 토큰 재발급 처리 중 서버 에러가 발생했습니다.",
    )


__all__ = [
    "handle_cognito_signup_error",
    "handle_cognito_verify_email_error",
    "handle_cognito_login_email_error",
    "handle_cognito_refresh_token_error",
]
