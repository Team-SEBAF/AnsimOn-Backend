from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials

from app.domain.user import schemas
from app.domain.user.dependency import bearer_scheme
from app.domain.user.service import user_service

router = APIRouter(
    prefix="/api/v1/users",
    tags=["User"],
)


@router.post(
    "/signup/email",
    summary="이메일 회원가입",
    description="이메일 회원가입을 수행합니다.",
    response_model=schemas.SignUpEmailResponse,
)
def signup_email(request: schemas.SignUpEmailRequest):
    return user_service.signup_email(request)


@router.post(
    "/verify-email",
    summary="이메일 회원가입 인증",
    description="이메일 회원가입 인증 코드를 검증합니다.",
    response_model=schemas.VerifyEmailResponse,
)
def verify_email(
    request: schemas.VerifyEmailRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    user_service._verify_access_token(access_token=credentials.credentials)
    return user_service.verify_email(request)


@router.post(
    "/resend-email-verification",
    summary="이메일 회원가입 인증 코드 재전송",
    description="이메일 회원가입 인증 코드를 재전송합니다.",
    status_code=200,
)
def resend_email_verification(
    request: schemas.ResendEmailVerificationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    user_service._verify_access_token(access_token=credentials.credentials)
    user_service.resend_email_verification(request)
    return JSONResponse(status_code=200, content={"message": "인증 코드가 재전송되었습니다."})


@router.post(
    "/login/email",
    summary="이메일 로그인",
    description="이메일 로그인을 수행합니다.",
    response_model=schemas.LoginEmailResponse,
)
def login_email(request: schemas.LoginEmailRequest):
    return user_service.login_email(request)


@router.get(
    "/me",
    summary="내 정보 조회",
    description="내 정보를 조회합니다.",
    response_model=schemas.MeResponse,
)
def get_me(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    return user_service.get_me(access_token=credentials.credentials)


@router.patch(
    "/me",
    summary="내 정보 수정",
    description="내 정보를 수정합니다.",
    response_model=schemas.MeResponse,
)
def update_me(
    request: schemas.UpdateMeRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    user_service._verify_access_token(access_token=credentials.credentials)
    return user_service.update_me(request, access_token=credentials.credentials)


@router.post(
    "/logout",
    summary="로그아웃",
    description="로그아웃을 수행합니다.",
    status_code=200,
)
def logout(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    user_service._verify_access_token(access_token=credentials.credentials)
    user_service.logout(access_token=credentials.credentials)
    return JSONResponse(status_code=200, content={"message": "로그아웃되었습니다."})
