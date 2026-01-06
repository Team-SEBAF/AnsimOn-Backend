from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings

if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
