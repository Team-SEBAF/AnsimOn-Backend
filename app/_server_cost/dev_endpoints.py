from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app._server_cost.db.service import server_cost_db_service
from app._server_cost.schemas import InfraStatusResponse
from app._server_cost.sse.service import server_cost_sse_service
from app.base.base_response import BaseSuccessResponse
from app.core.database import get_db

router = APIRouter(
    prefix="/api/v1/server_cost",
    tags=["Infra On/Off"],
)


@router.post(
    "/db/start",
    summary="DB 시작",
    description="RDS 인스턴스 시작을 요청합니다. 대략 3~6분 소요될 수 있습니다. 시작 중에는 status API에서 unavailable로 나타날 수 있습니다.",
    response_model=BaseSuccessResponse,
)
def start_db():
    server_cost_db_service.start_db()
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
    return server_cost_db_service.get_db_connection_status(db)


@router.post(
    "/db/stop",
    summary="DB 중지",
    description="RDS 인스턴스 중지를 요청합니다. 대략 8~15분 소요될 수 있습니다. 중지 중에는 status API에서 available로 나타날 수 있습니다.",
    response_model=BaseSuccessResponse,
)
def stop_db():
    server_cost_db_service.stop_db()
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
    server_cost_sse_service.start_sse()
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
    return server_cost_sse_service.get_sse_status()


@router.post(
    "/sse/stop",
    summary="SSE 서버 중지",
    description="SSE 서버를 끕니다. 대략 10초 소요될 수 있습니다. 중지 중에는 status API에서 available로 나타날 수 있습니다.",
    response_model=BaseSuccessResponse,
)
def sse_stop():
    server_cost_sse_service.stop_sse()
    return BaseSuccessResponse(
        message="SSE 서버 중지 요청을 보냈습니다. 대략 10초 소요될 수 있습니다. 중지 중에는 status API에서 available로 나타날 수 있습니다.",
    )


# 회원 탈퇴
# 사용하려면 AWS_PROFILE에 "CognitoDevAdminAccess" 권한 추가 필요
# @router.delete(
#     "/users",
#     summary="회원 탈퇴",
#     description="이메일로 Cognito 사용자를 삭제하고 DB의 users 행을 제거합니다.",
#     status_code=204,
# )
# def delete_dev_user(email: str, db: Session = Depends(get_db)):
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

#     user_sub = next(attr["Value"] for attr in resp["UserAttributes"] if attr["Name"] == "sub")

#     user_repo = UserRepository(db)
#     user_repo.delete_by_user_sub(user_sub)
#     db.commit()

#     cognito.admin_delete_user(
#         UserPoolId=settings.COGNITO_USER_POOL_ID,
#         Username=email,
#     )
