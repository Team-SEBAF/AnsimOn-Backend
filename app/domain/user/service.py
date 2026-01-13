import datetime
from uuid import UUID

from botocore.exceptions import ClientError

from app.core.aws import get_cognito_client
from app.core.settings import settings
from app.domain.user import schemas, utils
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
            is_verified=resp["UserConfirmed"],  # 거의 항상 False
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


user_service = UserService()
