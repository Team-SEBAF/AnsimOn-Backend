from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.base.base_response import BaseSuccessResponse
from app.core.aws import get_cognito_client
from app.core.database import get_db
from app.core.settings import settings
from app.dev.utils import _check_dev_environment, _get_dev_db_instance, rds
from app.domain.user.repos.user_repository import UserRepository

router = APIRouter(
    prefix="/api/v1/dev",
    tags=["Dev (개발용)"],
)


@router.post(
    "/db/start",
    summary="Dev DB 시작",
    description="Dev DB를 시작합니다. 실행에 5~10분 소요됩니다.",
)
def start_dev_db():
    _check_dev_environment()

    db = _get_dev_db_instance()
    db_id = db["DBInstanceIdentifier"]
    status = db["DBInstanceStatus"]

    if status == "stopped":
        rds.start_db_instance(DBInstanceIdentifier=db_id)

    return BaseSuccessResponse(
        message="Dev DB 시작 요청을 전송했습니다.",
    )


@router.delete(
    "/users",
    summary="회원 탈퇴",
    description="회원 탈퇴를 수행합니다.",
    status_code=204,
)
def delete_dev_user(email: str, db: Session = Depends(get_db)):
    _check_dev_environment()

    cognito = get_cognito_client()

    try:
        resp = cognito.admin_get_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "UserNotFoundException":
            raise HTTPException(
                status_code=404,
                detail="Cognito에서 해당 사용자 정보를 찾을 수 없습니다.",
            )
        raise

    user_sub = next((attr["Value"] for attr in resp["UserAttributes"] if attr["Name"] == "sub"))

    user_repo = UserRepository(db)
    user_repo.delete_by_user_sub(user_sub)
    db.commit()

    cognito.admin_delete_user(
        UserPoolId=settings.COGNITO_USER_POOL_ID,
        Username=email,
    )
    # 204는 No Content 상태 코드로, 응답 없음
