# ruff: noqa: F401, E402

from sqlalchemy.orm import declarative_base

# Base = 모든 모델의 기본 클래스
Base = declarative_base()

# 모든 모델을 import하여 alembic metadata에 등록
from app.domain.complaint import Complaint
from app.domain.evidence_message import EvidenceMessage
from app.domain.evidence_tracking import EvidenceTracking
from app.domain.evidence_voice import EvidenceVoice
from app.domain.user import User
