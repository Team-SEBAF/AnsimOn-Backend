from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.database import engine
from app.core.settings import settings

app = FastAPI(title="AnsimOn Backend")

# 우선 로컬 개발용만 허용 (나중에 환경변수로 빼기)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/check")
def check():
    return {"ok": True, "env": settings.env}


@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"db": "ok"}
