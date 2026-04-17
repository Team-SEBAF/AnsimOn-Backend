# ruff: noqa: F401, E402

from sqlalchemy.orm import declarative_base

# Base = 모든 모델의 기본 클래스
Base = declarative_base()

# 모든 모델을 import하여 alembic metadata에 등록
from app.domain.ai.models import Caching, Task
from app.domain.complaint import Complaint
from app.domain.document.models.document_model import Document
from app.domain.evidence_incident_log import (
    EvidenceIncidentLog,
    EvidenceIncidentLogFile,
    EvidenceIncidentLogFormData,
)
from app.domain.evidence_incident_log.models.incident_log_form_data_attachment_model import (
    IncidentLogFormDataAttachment,
)
from app.domain.evidence_message import EvidenceMessage
from app.domain.evidence_report_record import EvidenceReportRecord
from app.domain.evidence_victim import EvidenceVictim
from app.domain.evidence_voice import EvidenceVoice
from app.domain.timeline import Timeline, TimelineEvidence, TimelineManualEvidence
from app.domain.user import User
