import base64
import hashlib
import hmac
from dataclasses import dataclass
from uuid import UUID

from botocore.exceptions import ClientError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.base.base_error import CodeException
from app.core.aws import get_cognito_client
from app.core.settings import settings

bearer_scheme = HTTPBearer()


def get_cognito_secret_hash(username: str):
    msg = username + settings.COGNITO_CLIENT_ID
    digest = hmac.new(
        key=settings.COGNITO_CLIENT_SECRET.encode("utf-8"),
        msg=msg.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    return base64.b64encode(digest).decode()


@dataclass
class AuthUser:
    access_token: str
    user_sub: UUID
    email: str
    email_verified: bool
    name: str
    birthdate: str


def get_cognito_user_by_access_token(access_token: str) -> dict:
    cognito = get_cognito_client()

    try:
        return cognito.get_user(AccessToken=access_token)
    except ClientError as e:
        code = e.response["Error"]["Code"]

        if code == "NotAuthorizedException":
            raise CodeException(
                code="INVALID_ACCESS_TOKEN",
                message="액세스 토큰이 유효하지 않거나 만료되었습니다. 로그아웃 상태가 아니라면 리프레시 토큰을 사용해 새 액세스 토큰을 발급받아 주세요.",
                status_code=401,
            )

        # 그 외 Cognito 에러는 상위에서 처리
        raise


def parse_auth_user_from_cognito(
    access_token: str,
    resp: dict,
) -> AuthUser:
    attrs = {attr["Name"]: attr["Value"] for attr in resp["UserAttributes"]}

    return AuthUser(
        access_token=access_token,
        user_sub=UUID(attrs["sub"]),
        email=attrs["email"],
        email_verified=attrs["email_verified"] == "true",
        name=attrs.get("name"),
        birthdate=attrs.get("birthdate"),
    )


def fetch_auth_user_by_access_token(access_token: str) -> AuthUser:
    resp = get_cognito_user_by_access_token(access_token)
    return parse_auth_user_from_cognito(access_token, resp)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> AuthUser:
    return fetch_auth_user_by_access_token(credentials.credentials)


__all__ = [
    "get_cognito_secret_hash",
    "AuthUser",
    "get_current_user",
    "fetch_auth_user_by_access_token",
]
