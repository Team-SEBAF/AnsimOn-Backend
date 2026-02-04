from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import app.domain.user.errors as user_errors
from app.base import BaseSuccessResponse
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.user import schemas
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
    responses=user_errors.SIGNUP_EMAIL_ERRORS_RESPONSES,
)
def signup_email(
    request: schemas.SignUpEmailRequest,
):  # 한 API 실행 내에서 DB Session이 유지되도록 엔드포인트 레이어에서 생성해서 전달 + 사용 (서비스 레이어에서 생성하지 않음)
    return user_service.signup_email(request)


@router.post(
    "/verify-email",
    summary="이메일 회원가입 인증",
    description="이메일 회원가입 인증 코드를 검증합니다.",
    response_model=schemas.VerifyEmailResponse,
    responses=user_errors.VERIFY_EMAIL_ERRORS_RESPONSES,
)
def verify_email(
    request: schemas.VerifyEmailRequest,
):
    return user_service.verify_email(request)


@router.post(
    "/resend-email-verification",
    summary="이메일 회원가입 인증 코드 재전송",
    description="이메일 회원가입 인증 코드를 재전송합니다.",
    status_code=200,
    response_model=BaseSuccessResponse,
)
def resend_email_verification(
    request: schemas.ResendEmailVerificationRequest,
):
    user_service.resend_email_verification(request)
    return BaseSuccessResponse(message="인증 코드가 재전송되었습니다.")


@router.post(
    "/login/email",
    summary="이메일 회원 로그인",
    description="이메일 회원 로그인을 수행합니다.",
    response_model=schemas.LoginTokenResponse,
    responses=user_errors.LOGIN_EMAIL_ERRORS_RESPONSES,
)
def login_email(request: schemas.LoginEmailRequest):
    return user_service.login_email(request)


@router.get(
    "/me",
    summary="내 정보 조회",
    description="내 정보를 조회합니다.",
    response_model=schemas.MeResponse,
)
def get_me(current_user: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_service.get_me(current_user, db)


@router.patch(
    "/me",
    summary="내 정보 수정",
    description="내 정보를 수정합니다.",
    response_model=schemas.MeResponse,
)
def update_me(
    request: schemas.UpdateMeRequest,
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.update_me(request, current_user, db)


@router.post(
    "/logout",
    summary="이메일 회원 로그아웃",
    description="이메일 회원 로그아웃을 수행합니다.",
    status_code=200,
    response_model=BaseSuccessResponse,
)
def logout(current_user: AuthUser = Depends(get_current_user)):
    user_service.logout(current_user)
    return BaseSuccessResponse(message="로그아웃되었습니다.")


@router.post(
    "/token/refresh",
    summary="리프레시 토큰으로 새 액세스 토큰과 ID 토큰 발급",
    description="리프레시 토큰을 사용해 새 액세스 토큰과 ID 토큰을 발급받습니다.",
    response_model=schemas.RefreshTokenResponse,
    responses=user_errors.REFRESH_TOKEN_ERRORS_RESPONSES,
)
def refresh_token(
    request: schemas.RefreshTokenRequest,
):
    return user_service.refresh_token(request)


@router.post(
    "/google/callback",
    summary="Google 로그인 코드로 토큰 발급",
    description="Google 로그인 코드로 토큰을 발급받습니다.",
    response_model=schemas.LoginTokenResponse,
)
def google_callback(
    request: schemas.GoogleCallbackRequest,
):
    return user_service.google_callback(request)
