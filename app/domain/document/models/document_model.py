from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.base.base_db import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    complaint_id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        ForeignKey("complaints.complaint_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    complaint_form_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    statement_form_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    need_complaint_pdf_regeneration: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="고소장 PDF 재생성 필요 여부",
    )
    need_statement_pdf_regeneration: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="진술서 PDF 재생성 필요 여부",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
