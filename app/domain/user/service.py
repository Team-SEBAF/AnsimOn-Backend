import datetime
from uuid import UUID

from botocore.exceptions import ClientError

from app.core.aws import get_cognito_client
from app.core.settings import settings
from app.domain.user import schemas, utils
from app.domain.user.exception import handle_cognito_signup_error


class UserService:
    def signup_email(self, req: schemas.SignUpEmailRequest) -> schemas.SignUpEmailResponse:
        cognito = get_cognito_client()

        secret_hash = utils.get_secret_hash(
            username=req.email,
            client_id=settings.COGNITO_CLIENT_ID,
            client_secret=settings.COGNITO_CLIENT_SECRET,
        )

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
            print(resp)
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


user_service = UserService()
