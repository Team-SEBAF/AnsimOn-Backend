from typing import Literal

# from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends

# from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app._server_cost.db_utils import _get_rds_client, _get_rds_instance_by_tags
from app._server_cost.sse_utils import sse_is_available, sse_set_desired_count
from app.base.base_response import BaseResponse, BaseSuccessResponse

# from app.core.aws import delete_s3_objects_by_prefix, get_cognito_client
from app.core.database import get_db

# from app.core.settings import settings
# from app.domain.user.repos.user_repository import UserRepository

router = APIRouter(
    prefix="/api/v1/server_cost",
    tags=["Server Cost"],
)


class InfraStatusResponse(BaseResponse):
    """인프라(DB, SSE 등) 사용 가능 여부. available / unavailable 로 구분."""

    status: Literal["available", "unavailable"]


@router.post(
    "/db/start",
    summary="DB 시작",
    description="RDS 인스턴스 시작을 요청합니다. 대략 3~6분 소요될 수 있습니다. 시작 중에는 status API에서 unavailable로 나타날 수 있습니다.",
    response_model=BaseSuccessResponse,
)
def start_db():
    db = _get_rds_instance_by_tags()
    db_id = db["DBInstanceIdentifier"]
    status = db["DBInstanceStatus"]

    if status == "stopped":
        _get_rds_client().start_db_instance(DBInstanceIdentifier=db_id)

    return BaseSuccessResponse(
        message="DB 시작 요청을 전송했습니다. 대략 3~6분 소요될 수 있습니다. 시작 중에는 status API에서 unavailable로 나타날 수 있습니다.",
    )


@router.get(
    "/db/status",
    summary="DB 실행 여부 조회",
    description="애플리케이션 DB 연결 가능 여부를 조회합니다.",
    response_model=InfraStatusResponse,
)
def get_db_status(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return InfraStatusResponse(status="available")
    except OperationalError:
        return InfraStatusResponse(status="unavailable")


@router.post(
    "/db/stop",
    summary="DB 중지",
    description="RDS 인스턴스 중지를 요청합니다. 대략 8~15분 소요될 수 있습니다. 중지 중에는 status API에서 available로 나타날 수 있습니다.",
    response_model=BaseSuccessResponse,
)
def stop_db():
    db = _get_rds_instance_by_tags()
    db_id = db["DBInstanceIdentifier"]
    status = db["DBInstanceStatus"]

    if status == "available":
        _get_rds_client().stop_db_instance(DBInstanceIdentifier=db_id)

    return BaseSuccessResponse(
        message="DB 중지 요청을 전송했습니다. 대략 8~15분 소요될 수 있습니다. 중지 중에는 status API에서 available로 나타날 수 있습니다.",
    )


@router.post(
    "/sse/start",
    summary="SSE 서버 시작",
    description="SSE 서버를 켭니다. 대략 1분 정도 소요될 수 있습니다. 시작 중에는 status API에서 unavailable로 나타날 수 있습니다.",
    response_model=BaseSuccessResponse,
)
def sse_start():
    sse_set_desired_count(1)
    return BaseSuccessResponse(
        message="SSE 서버 시작 요청을 보냈습니다. 대략 1분 정도 소요될 수 있습니다. 시작 중에는 status API에서 unavailable로 나타날 수 있습니다.",
    )


@router.get(
    "/sse/status",
    summary="SSE 서버 실행 여부 조회",
    description="SSE 서버가 실행 중이면 available, 아니면 unavailable입니다. DB status API와 동일한 형식입니다.",
    response_model=InfraStatusResponse,
)
def sse_status():
    if sse_is_available():
        return InfraStatusResponse(status="available")
    return InfraStatusResponse(status="unavailable")


@router.post(
    "/sse/stop",
    summary="SSE 서버 중지",
    description="SSE 서버를 끕니다. 대략 10초 소요될 수 있습니다. 중지 중에는 status API에서 available로 나타날 수 있습니다.",
    response_model=BaseSuccessResponse,
)
def sse_stop():
    sse_set_desired_count(0)
    return BaseSuccessResponse(
        message="SSE 서버 중지 요청을 보냈습니다. 대략 10초 소요될 수 있습니다. 중지 중에는 status API에서 available로 나타날 수 있습니다.",
    )


# 회원 탈퇴
# 사용하려면 AWS_PROFILE에 "CognitoDevAdminAccess" 권한 추가 필요
# @router.delete(
#     "/users",
#     summary="회원 탈퇴",
#     description="회원 탈퇴를 수행합니다.",
#     status_code=204,
# )
# def delete_user_by_email(email: str, db: Session = Depends(get_db)):
#     cognito = get_cognito_client()

#     try:
#         resp = cognito.admin_get_user(
#             UserPoolId=settings.COGNITO_USER_POOL_ID,
#             Username=email,
#         )
#     except ClientError as e:
#         code = e.response["Error"]["Code"]
#         if code == "UserNotFoundException":
#             raise HTTPException(
#                 status_code=404,
#                 detail="Cognito에서 해당 사용자 정보를 찾을 수 없습니다.",
#             )
#         raise

#     user_sub = next((attr["Value"] for attr in resp["UserAttributes"] if attr["Name"] == "sub"))

#     if settings.S3_BUCKET_NAME:
#         delete_s3_objects_by_prefix(settings.S3_BUCKET_NAME, f"{user_sub}/")

#     user_repo = UserRepository(db)
#     user_repo.delete_by_user_sub(user_sub)
#     db.commit()

#     cognito.admin_delete_user(
#         UserPoolId=settings.COGNITO_USER_POOL_ID,
#         Username=email,
#     )
