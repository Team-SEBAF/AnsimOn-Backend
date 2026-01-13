from fastapi import APIRouter

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
