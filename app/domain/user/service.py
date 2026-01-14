import datetime
from uuid import UUID

from botocore.exceptions import ClientError

from app.base import InternalServerErrorException
from app.core.aws import get_cognito_client
from app.core.settings import settings
from app.domain.user import schemas, utils
from app.domain.user.dependency import handle_cognito_access_token_error
from app.domain.user.exception import (
    handle_cognito_login_email_error,
    handle_cognito_signup_error,
    handle_cognito_verify_email_error,
)


class UserService:
    @staticmethod
    def _init(email: str):
        cognito = get_cognito_client()

        secret_hash = utils.get_secret_hash(
            username=email,
            client_id=settings.COGNITO_CLIENT_ID,
            client_secret=settings.COGNITO_CLIENT_SECRET,
        )

        return cognito, secret_hash

    @staticmethod
    def _verify_access_token(access_token: str) -> bool:
        cognito = get_cognito_client()

        try:
            cognito.get_user(AccessToken=access_token)
        except ClientError as e:
            raise handle_cognito_access_token_error(e)

        return True

    def signup_email(self, req: schemas.SignUpEmailRequest) -> schemas.SignUpEmailResponse:
        cognito, secret_hash = self._init(req.email)

        try:
            resp = cognito.sign_up(
                ClientId=settings.COGNITO_CLIENT_ID,
                SecretHash=secret_hash,
                Username=req.email,
                Password=req.password,
                UserAttributes=[
                    {"Name": "email", "Value": req.email},
                    {"Name": "name", "Value": req.name},
                    {"Name": "birthdate", "Value": req.birthdate.isoformat()},
                ],
            )
        except ClientError as e:
            raise handle_cognito_signup_error(e)

        return schemas.SignUpEmailResponse(
            user_sub=UUID(resp["UserSub"]),
            email=req.email,
            is_verified=resp["UserConfirmed"],
            name=req.name,
            birthdate=req.birthdate,
            is_legal_representative=req.is_legal_representative,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

    def verify_email(self, req: schemas.VerifyEmailRequest) -> schemas.VerifyEmailResponse:
        cognito, secret_hash = self._init(req.email)

        try:
            cognito.confirm_sign_up(
                ClientId=settings.COGNITO_CLIENT_ID,
                SecretHash=secret_hash,
                Username=req.email,
                ConfirmationCode=req.code,
            )
        except ClientError as e:
            raise handle_cognito_verify_email_error(e)

        return schemas.VerifyEmailResponse(
            email=req.email,
            is_verified=True,
        )

    def resend_email_verification(self, req: schemas.ResendEmailVerificationRequest):
        cognito, secret_hash = self._init(req.email)

        cognito.resend_confirmation_code(
            ClientId=settings.COGNITO_CLIENT_ID,
            SecretHash=secret_hash,
            Username=req.email,
        )

    def login_email(self, req: schemas.LoginEmailRequest) -> schemas.LoginEmailResponse:
        cognito, secret_hash = self._init(req.email)

        try:
            resp = cognito.initiate_auth(
                ClientId=settings.COGNITO_CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": req.email,
                    "PASSWORD": req.password,
                    "SECRET_HASH": secret_hash,
                },
            )
        except ClientError as e:
            raise handle_cognito_login_email_error(e)

        auth = resp["AuthenticationResult"]

        return schemas.LoginEmailResponse(
            access_token=auth["AccessToken"],
            id_token=auth["IdToken"],
            refresh_token=auth["RefreshToken"],
            expires_in=int(auth["ExpiresIn"]),
            token_type=auth["TokenType"],
        )

    def get_me(self, access_token: str) -> schemas.MeResponse:
        cognito = get_cognito_client()

        try:
            resp = cognito.get_user(AccessToken=access_token)

        except ClientError as e:
            raise handle_cognito_access_token_error(e)

        # Cognito attribute list → dict 변환
        attrs = {attr["Name"]: attr["Value"] for attr in resp["UserAttributes"]}

        return schemas.MeResponse(
            user_sub=UUID(attrs.get("sub")),
            email=attrs.get("email"),
            is_verified=attrs.get("email_verified") == "true",
            name=attrs.get("name"),
            birthdate=attrs.get("birthdate"),
            # TODO: 일단 임시값 리턴하고 DB 연결하면 처리
            is_legal_representative=False,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

    def update_me(
        self,
        request: schemas.UpdateMeRequest,
        access_token: str,
    ) -> schemas.MeResponse:
        cognito = get_cognito_client()

        attributes: list[dict[str, str]] = []

        if request.name is not None:
            attributes.append({"Name": "name", "Value": request.name})

        if request.birthdate is not None:
            attributes.append(
                {
                    "Name": "birthdate",
                    "Value": request.birthdate.isoformat(),  # YYYY-MM-DD
                }
            )

        # TODO: 일단 패스하고 DB 연결하면 처리
        if request.is_legal_representative is not None:
            pass

        # 변경할 값이 없으면 그냥 현재 정보 리턴
        if not attributes:
            return self.get_me(access_token=access_token)

        try:
            cognito.update_user_attributes(
                AccessToken=access_token,
                UserAttributes=attributes,
            )
        except ClientError:
            raise InternalServerErrorException(
                message="내 정보 수정 처리 중 서버 에러가 발생했습니다.",
            )

        # 업데이트 후 최신 정보 다시 조회해서 반환
        return self.get_me(access_token=access_token)


user_service = UserService()
