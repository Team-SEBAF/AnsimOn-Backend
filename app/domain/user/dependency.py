from botocore.exceptions import ClientError
from fastapi.security import HTTPBearer

from app.base import CodeException

bearer_scheme = HTTPBearer()


def handle_cognito_access_token_error(e: ClientError):
    code = e.response["Error"]["Code"]

    if code == "NotAuthorizedException":
        raise CodeException(
            code="INVALID_ACCESS_TOKEN",
            message="유효하지 않은 액세스 토큰입니다. 리프레시 토큰을 사용해 새로운 액세스 토큰을 발급받아 주세요.",
            status_code=401,
        )

    # 나머지는 서버 에러
    raise CodeException(
        code="INTERNAL_SERVER_ERROR",
        message="액세스 토큰 검증 중 오류가 발생했습니다.",
        status_code=500,
    )


__all__ = ["bearer_scheme", "handle_cognito_access_token_error"]
