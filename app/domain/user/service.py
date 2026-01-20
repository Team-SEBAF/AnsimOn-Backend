import datetime
from uuid import UUID

from botocore.exceptions import ClientError
from jose import jwt

import app.domain.user.errors as user_errors
from app.core.auth import AuthUser, fetch_auth_user_by_access_token, get_cognito_secret_hash
from app.core.aws import get_cognito_client
from app.core.settings import settings
from app.domain.user import schemas


class UserService:
    def signup_email(self, req: schemas.SignUpEmailRequest) -> schemas.SignUpEmailResponse:
        cognito = get_cognito_client()
        secret_hash = get_cognito_secret_hash(req.email)

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
            raise user_errors.handle_signup_email_error(e)

        return schemas.SignUpEmailResponse(
            user_sub=UUID(resp["UserSub"]),
            email=req.email,
            email_verified=resp["UserConfirmed"],
            name=req.name,
            birthdate=req.birthdate,
            is_legal_representative=req.is_legal_representative,  # TODO
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

    def verify_email(self, req: schemas.VerifyEmailRequest) -> schemas.VerifyEmailResponse:
        cognito = get_cognito_client()
        secret_hash = get_cognito_secret_hash(req.email)

        try:
            cognito.confirm_sign_up(
                ClientId=settings.COGNITO_CLIENT_ID,
                SecretHash=secret_hash,
                Username=req.email,
                ConfirmationCode=req.code,
            )
        except ClientError as e:
            raise user_errors.handle_verify_email_error(e)

        return schemas.VerifyEmailResponse(
            email=req.email,
            email_verified=True,
        )

    def resend_email_verification(self, req: schemas.ResendEmailVerificationRequest):
        cognito = get_cognito_client()
        secret_hash = get_cognito_secret_hash(req.email)

        cognito.resend_confirmation_code(
            ClientId=settings.COGNITO_CLIENT_ID,
            SecretHash=secret_hash,
            Username=req.email,
        )

    def login_email(self, req: schemas.LoginEmailRequest) -> schemas.LoginEmailResponse:
        cognito = get_cognito_client()
        secret_hash = get_cognito_secret_hash(req.email)

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
            raise user_errors.handle_login_email_error(e)

        auth = resp["AuthenticationResult"]

        return schemas.LoginEmailResponse(
            access_token=auth["AccessToken"],
            id_token=auth["IdToken"],
            refresh_token=auth["RefreshToken"],
            expires_in=int(auth["ExpiresIn"]),
            token_type=auth["TokenType"],
        )

    def get_me(self, current_user: AuthUser) -> schemas.MeResponse:
        return schemas.MeResponse(
            user_sub=current_user.user_sub,
            email=current_user.email,
            email_verified=current_user.email_verified,
            name=current_user.name,
            birthdate=current_user.birthdate,
            # TODO: 일단 임시값 리턴하고 DB 연결하면 처리
            is_legal_representative=False,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )

    def update_me(
        self,
        request: schemas.UpdateMeRequest,
        current_user: AuthUser,
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
            return self.get_me(current_user=current_user)

        cognito.update_user_attributes(
            AccessToken=current_user.access_token,
            UserAttributes=attributes,
        )

        # 업데이트 후 최신 정보 다시 조회해서 반환
        new_current_user = fetch_auth_user_by_access_token(current_user.access_token)
        return self.get_me(current_user=new_current_user)

    def logout(self, current_user: AuthUser):
        cognito = get_cognito_client()

        try:
            cognito.global_sign_out(
                AccessToken=current_user.access_token,
            )
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "NotAuthorizedException":
                # 이미 만료됐거나 무효한 토큰
                # → 로그아웃은 idempotent 하게 성공 처리해도 됨
                return

            raise

    def refresh_token(
        self,
        request: schemas.RefreshTokenRequest,
    ) -> schemas.RefreshTokenResponse:
        cognito = get_cognito_client()

        # ID 토큰으로부터 username 추출
        payload = jwt.get_unverified_claims(request.id_token)
        username = payload["cognito:username"]

        secret_hash = get_cognito_secret_hash(username=username)

        try:
            resp = cognito.initiate_auth(
                ClientId=settings.COGNITO_CLIENT_ID,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": request.refresh_token,
                    "SECRET_HASH": secret_hash,
                },
            )
        except ClientError as e:
            raise user_errors.handle_refresh_token_error(e)

        auth = resp["AuthenticationResult"]

        return schemas.RefreshTokenResponse(
            access_token=auth["AccessToken"],
            id_token=auth["IdToken"],
            expires_in=int(auth["ExpiresIn"]),
            token_type=auth["TokenType"],
        )


user_service = UserService()
