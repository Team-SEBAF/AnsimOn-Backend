from botocore.exceptions import ClientError
from fastapi import HTTPException
from jose import jwt
from sqlalchemy.orm import Session

from app.core.auth import AuthUser, fetch_auth_user_by_access_token, get_cognito_secret_hash
from app.core.aws import get_cognito_client
from app.core.settings import settings
from app.domain.complaint import Complaint, ComplaintRepository, ComplaintStep
from app.domain.user import User, UserRepository, schemas
from app.domain.user import errors as user_errors


class UserService:
    def _get_db_user(
        self,
        db: Session,
        user_sub: str,
    ) -> User:
        user_repo = UserRepository(db)
        db_user = user_repo.get(user_sub)
        if not db_user:
            raise HTTPException(
                status_code=404,
                detail="데이터베이스에서 해당 사용자 정보를 찾을 수 없습니다.",
            )
        return db_user

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
            user_sub=resp["UserSub"],
            email=req.email,
            email_verified=False,
            name=req.name,
            birthdate=req.birthdate,
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

    def login_email(
        self, req: schemas.LoginEmailRequest, db: Session
    ) -> schemas.LoginEmailResponse:
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

        user_repo = UserRepository(db)
        user = user_repo.get_by_email(req.email)
        if not user:
            # 이메일 인증 후 최초 로그인 시에만 수행
            payload = jwt.get_unverified_claims(auth["IdToken"])
            user_sub = payload["sub"]

            user = user_repo.create(
                User(
                    user_sub=user_sub,
                    email=req.email,
                )
            )
            db.flush()  # 현재 session에 쌓인 변경 사항을 DB에 반영 (트랜잭션 종료는 아님)

            complaint_repo = ComplaintRepository(db)
            complaint_repo.create(
                Complaint(
                    user_sub=user_sub,
                    step=ComplaintStep.EVIDENCE,
                )
            )

            db.commit()  # 트랜잭션을 성공적으로 확정하고 종료
            db.refresh(user)

        return schemas.LoginEmailResponse(
            access_token=auth["AccessToken"],
            id_token=auth["IdToken"],
            refresh_token=auth["RefreshToken"],
            expires_in=int(auth["ExpiresIn"]),
            token_type=auth["TokenType"],
        )

    def get_me(self, current_user: AuthUser, db: Session) -> schemas.MeResponse:
        db_user = self._get_db_user(db, current_user.user_sub)

        complaint_repo = ComplaintRepository(db)
        db_complaint = complaint_repo.get_by_user_sub(current_user.user_sub)

        return schemas.MeResponse(
            user_sub=current_user.user_sub,
            email=current_user.email,
            email_verified=current_user.email_verified,
            name=current_user.name,
            birthdate=current_user.birthdate,
            created_at=db_user.created_at,
            complaint_id=db_complaint.complaint_id,
        )

    def update_me(
        self,
        request: schemas.UpdateMeRequest,
        current_user: AuthUser,
        db: Session,
    ) -> schemas.MeResponse:
        cognito = get_cognito_client()

        cognito_attributes: list[dict[str, str]] = []

        if request.name is not None:
            cognito_attributes.append({"Name": "name", "Value": request.name})

        if request.birthdate is not None:
            cognito_attributes.append(
                {
                    "Name": "birthdate",
                    "Value": request.birthdate.isoformat(),  # YYYY-MM-DD
                }
            )

        if cognito_attributes:
            cognito.update_user_attributes(
                AccessToken=current_user.access_token,
                UserAttributes=cognito_attributes,
            )

        # 업데이트 후 최신 정보 다시 조회해서 반환
        new_current_user = fetch_auth_user_by_access_token(current_user.access_token)
        return self.get_me(new_current_user, db)

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
