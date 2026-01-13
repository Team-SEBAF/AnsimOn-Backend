from fastapi import APIRouter
from fastapi.responses import JSONResponse

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
)
def signup_email(request: schemas.SignUpEmailRequest):
    return user_service.signup_email(request)


@router.post(
    "/signup/email/verify",
    summary="이메일 회원가입 인증",
    description="이메일 회원가입 인증 코드를 검증합니다.",
    response_model=schemas.VerifyEmailResponse,
)
def signup_email_verify(request: schemas.VerifyEmailRequest):
    return user_service.verify_email(request)


@router.post(
    "/signup/email/resend-verification",
    summary="이메일 회원가입 인증 코드 재전송",
    description="이메일 회원가입 인증 코드를 재전송합니다.",
    status_code=200,
)
def resend_email_verification(request: schemas.ResendEmailVerificationRequest):
    user_service.resend_email_verification(request)
    return JSONResponse(status_code=200, content={"message": "인증 코드가 재전송되었습니다."})
