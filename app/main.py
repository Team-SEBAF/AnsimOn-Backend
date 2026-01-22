from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.base.base_error import register_exception_handlers
from app.core.settings import settings
from app.domain.user.endpoints import router as user_router

root_path = "/prod" if settings.env == "prod" else ""

app = FastAPI(title="AnsimOn Backend", root_path=root_path)

# 우선 로컬 개발용만 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 예외 핸들러 등록
register_exception_handlers(app)

app.include_router(user_router)

handler = Mangum(app)
