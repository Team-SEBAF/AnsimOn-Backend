from copy import deepcopy
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.complaint import Complaint
from app.domain.evidence.constant import EvidenceType
from app.domain.evidence_incident_log.models.evidence_incident_log_model import (
    EvidenceIncidentLogType,
)
from app.domain.evidence_incident_log.repos.evidence_incident_log_repository import (
    EvidenceIncidentLogFileRepository,
    EvidenceIncidentLogRepository,
)
from app.domain.evidence_incident_log.service import evidence_incident_log_service
from app.domain.evidence_message.repos.evidence_message_repository import (
    EvidenceMessageRepository,
)
from app.domain.evidence_report_record.repos.evidence_report_record_repository import (
    EvidenceReportRecordRepository,
)
from app.domain.evidence_victim.repos.evidence_victim_repository import (
    EvidenceVictimRepository,
)
from app.domain.evidence_voice.repos.evidence_voice_repository import (
    EvidenceVoiceRepository,
)
from app.domain.timeline.repos import (
    TimelineEvidenceRepository,
    TimelineManualEvidenceRepository,
    TimelineRepository,
)


def _format_evidence_numstring(date: str, time: str, index: int, sub_index: int) -> str:
    """증거 번호 생성. date=YYYY-MM-DD, time=HH:MM -> YYYYMMDD-HHMM-index-sub_index."""
    date_compact = date.replace("-", "") if date else ""
    time_compact = time.replace(":", "") if time else ""
    return f"{date_compact}-{time_compact}-{index}-{sub_index}"


class TimelineDownloadService:
    def _get_evidence_s3_info_for_row(
        self,
        row,
        complaint: Complaint,
        message_repo,
        victim_repo,
        voice_repo,
        report_record_repo,
        incident_log_repo,
        incident_log_file_repo,
        manual_repo,
        db,
    ) -> str | None | dict:
        """
        timeline_evidence row에서 s3 정보 추출.
        Returns: s3_key (str) | None | {"main": s3_key, "attachments": [...]} (FORM_DATA에 첨부 있을 때만)
        """
        if row.is_original_evidence:
            if row.evidence_type == EvidenceType.MESSAGE.value:
                entity = message_repo.get(row.referenced_evidence_id)
                return entity.s3_key if entity else None
            if row.evidence_type == EvidenceType.VICTIM.value:
                entity = victim_repo.get(row.referenced_evidence_id)
                return entity.s3_key if entity else None
            if row.evidence_type == EvidenceType.VOICE.value:
                entity = voice_repo.get(row.referenced_evidence_id)
                return entity.s3_key if entity else None
            if row.evidence_type == EvidenceType.REPORT_RECORD.value:
                entity = report_record_repo.get(row.referenced_evidence_id)
                return entity.s3_key if entity else None
            if row.evidence_type == EvidenceType.INCIDENT_LOG.value:
                log = incident_log_repo.get(row.referenced_evidence_id)
                if not log:
                    return None
                if log.type == EvidenceIncidentLogType.FILE:
                    f = incident_log_file_repo.get(log.incident_log_id)
                    return f.s3_key if f else None
                if log.type == EvidenceIncidentLogType.FORM_DATA:
                    (
                        main_key,
                        attachments,
                    ) = evidence_incident_log_service.ensure_form_data_pdf_and_get_s3_key(
                        incident_log_id=row.referenced_evidence_id,
                        complaint=complaint,
                        db=db,
                    )
                    if attachments:
                        return {"main": main_key, "attachments": attachments}
                    return main_key
                return None
        else:
            if row.referenced_manual_evidence_id:
                entity = manual_repo.get(row.referenced_manual_evidence_id)
                return entity.s3_key if entity else None
        return None

    def get_timeline_for_download(self, complaint: Complaint, db: Session) -> dict:
        """
        ZIP/PDF 생성용 타임라인 JSON.
        - has_thumbnail, thumbnail_url, duration_seconds 제거
        - evidences_numstring_s3_key_list 추가 (증거번호 -> s3_key | {"main", "attachments"} 매핑)
        """
        timeline_repo = TimelineRepository(db)
        timeline = timeline_repo.get_by_complaint_id(complaint.complaint_id)

        data = deepcopy(timeline.timeline_json)
        timeline_id = timeline.id
        timeline_evidence_repo = TimelineEvidenceRepository(db)

        message_repo = EvidenceMessageRepository(db)
        victim_repo = EvidenceVictimRepository(db)
        voice_repo = EvidenceVoiceRepository(db)
        report_record_repo = EvidenceReportRecordRepository(db)
        incident_log_repo = EvidenceIncidentLogRepository(db)
        incident_log_file_repo = EvidenceIncidentLogFileRepository(db)
        manual_repo = TimelineManualEvidenceRepository(db)

        for dg in data.get("items", []):
            date_str = dg.get("date", "")
            for evt in dg.get("events", []):
                time_str = evt.get("time", "")
                for ev in evt.get("evidences", []):
                    ev_id = ev.get("timeline_evidence_id") or ev.get("id")
                    if not ev_id:
                        continue
                    try:
                        timeline_evidence_id = UUID(ev_id) if isinstance(ev_id, str) else ev_id
                    except (ValueError, TypeError):
                        continue

                    ev.pop("has_thumbnail", None)
                    ev.pop("thumbnail_url", None)
                    ev.pop("duration_seconds", None)

                    index = ev.get("index", 1)
                    rows = timeline_evidence_repo.list_by_timeline_evidence_id(
                        timeline_id, timeline_evidence_id
                    )

                    numstring_s3_map: dict = {}
                    for sub_idx, row in enumerate(rows, start=1):
                        numstring = _format_evidence_numstring(date_str, time_str, index, sub_idx)
                        s3_info = self._get_evidence_s3_info_for_row(
                            row=row,
                            complaint=complaint,
                            message_repo=message_repo,
                            victim_repo=victim_repo,
                            voice_repo=voice_repo,
                            report_record_repo=report_record_repo,
                            incident_log_repo=incident_log_repo,
                            incident_log_file_repo=incident_log_file_repo,
                            manual_repo=manual_repo,
                            db=db,
                        )
                        numstring_s3_map[numstring] = s3_info

                    ev["evidences_numstring_s3_key_list"] = numstring_s3_map

        return data


timeline_download_service = TimelineDownloadService()
