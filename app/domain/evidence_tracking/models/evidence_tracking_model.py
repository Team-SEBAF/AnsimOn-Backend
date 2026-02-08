from uuid import UUID, uuid4

from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base.base_db import Base
from app.domain.evidence.models.evidence_base_model import Evidence


class EvidenceTracking(Base, Evidence):
    __tablename__ = "evidence_trackings"

    tracking_id: Mapped[UUID] = mapped_column(
        PostgresUUID[UUID](as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
