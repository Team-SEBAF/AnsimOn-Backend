from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_db import Base


class Caching(Base):
    __tablename__ = "cachings"

    hash_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
