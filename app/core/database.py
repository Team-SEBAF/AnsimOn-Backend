from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.settings import settings

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# engine = DB 서버와의 연결 풀
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# Session = 실제 트랜잭션 단위 작업자
# sessionmaker = Session 클래스를 생성하는 팩토리 함수
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base = 모든 모델의 기본 클래스
Base = declarative_base()

# 모든 모델을 import하여 alembic metadata에 등록
