from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.exception_handlers import register_exception_handlers
from app.core.settings import settings
from app.domain.user.endpoints import router as user_router

app = FastAPI(title="AnsimOn Backend")

# 우선 로컬 개발용만 허용 (나중에 환경변수로 빼기)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.get("/check")
# def check():
#     return {"ok": True, "env": settings.env}


# @app.get("/health/db")
# def health_db():
#     with engine.connect() as conn:
#         conn.execute(text("SELECT 1"))
#     return {"db": "ok"}

# 예외 핸들러 등록
register_exception_handlers(app)

app.include_router(user_router)
