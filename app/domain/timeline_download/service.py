import mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy.orm import Session

from app.core.aws import (
    download_s3_object_with_metadata,
    generate_presigned_get_url,
    head_s3_object,
    upload_fileobj,
)
from app.core.settings import settings
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


def _ext_from_content_type(content_type: str | None, default: str = ".bin") -> str:
    """Content-Type에서 확장자 추출."""
    if not content_type:
        return default
    ct = content_type.split(";")[0].strip().lower()
    return mimetypes.guess_extension(ct) or default


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

    def _collect_zip_entries(
        self, timeline_data: dict, evidence_root: str
    ) -> list[tuple[str, str]]:
        """
        timeline_data에서 (zip 내 경로 suffix, s3_key) 쌍 수집.
        경로 suffix는 확장자 제외 (예: 20260222-1000-1-1, 20260222-1000-1-1/설명).
        확장자는 다운로드 시 Content-Type에서 추출.
        """
        entries: list[tuple[str, str]] = []
        for dg in timeline_data.get("items", []):
            for evt in dg.get("events", []):
                for ev in evt.get("evidences", []):
                    numstring_map = ev.get("evidences_numstring_s3_key_list") or {}
                    for numstring, s3_info in numstring_map.items():
                        if s3_info is None:
                            continue
                        if isinstance(s3_info, str):
                            path_suffix = numstring
                            entries.append((path_suffix, s3_info))
                        elif isinstance(s3_info, dict):
                            main_key = s3_info.get("main")
                            attachments = s3_info.get("attachments") or []
                            if main_key:
                                entries.append((f"{numstring}/설명", main_key))
                            for i, att_key in enumerate(attachments, start=1):
                                entries.append((f"{numstring}/첨부 자료/첨부자료 {i}", att_key))
        return entries

    def _download_one(self, s3_key: str) -> tuple[str, bytes, str | None]:
        """S3에서 단일 객체 다운로드. (s3_key, bytes, content_type) 반환."""
        data, meta = download_s3_object_with_metadata(settings.S3_BUCKET_NAME, s3_key)
        return s3_key, data, meta.get("ContentType")

    def create_download_zip(self, complaint: Complaint, db: Session) -> tuple[bytes, str]:
        """
        다운로드 ZIP(대조 증거 모음 + 타임라인 PDF) 생성.
        need_evidence_collection_regeneration 또는 S3에 없으면 재생성.
        Returns: (zip_bytes, s3_key)
        """
        timeline_repo = TimelineRepository(db)
        timeline = timeline_repo.get_by_complaint_id(complaint.complaint_id)
        s3_key = (
            f"{complaint.user_sub}/complaints/{complaint.complaint_id}/"
            "timeline-download/download.zip"
        )
        exists_in_s3 = head_s3_object(settings.S3_BUCKET_NAME, s3_key) is not None
        need_regenerate = (
            timeline.need_evidence_collection_regeneration if timeline else True
        ) or not exists_in_s3

        if not need_regenerate:
            return b"", s3_key

        timeline_data = self.get_timeline_for_download(complaint=complaint, db=db)
        date_str = datetime.now(timezone.utc).strftime("%y%m%d")
        zip_root = f"안심온_증거분석타임라인_{date_str}"
        evidence_root = f"{zip_root}/대조 증거 모음"
        entries = self._collect_zip_entries(timeline_data, evidence_root)

        # 병렬 다운로드 (동일 s3_key 중복 다운로드 방지)
        unique_s3_keys = list({s3_key for _, s3_key in entries})
        s3_key_to_bytes_and_ext: dict[str, tuple[bytes, str]] = {}
        if unique_s3_keys:
            with ThreadPoolExecutor(max_workers=min(10, len(unique_s3_keys))) as executor:
                futures = {executor.submit(self._download_one, k): k for k in unique_s3_keys}
                for future in as_completed(futures):
                    try:
                        k, data, ct = future.result()
                        ext = _ext_from_content_type(ct)
                        s3_key_to_bytes_and_ext[k] = (data, ext)
                    except Exception:
                        raise

        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
            # 빈 폴더: 타임라인_PDF
            zf.writestr(f"{zip_root}/타임라인_PDF/", "")
            for path_suffix, s3_key in entries:
                if pair := s3_key_to_bytes_and_ext.get(s3_key):
                    data, ext = pair
                    zip_path = f"{evidence_root}/{path_suffix}{ext}"
                    zf.writestr(zip_path, data)

        buffer.seek(0)
        zip_bytes = buffer.getvalue()

        upload_fileobj(
            fileobj=BytesIO(zip_bytes),
            bucket=settings.S3_BUCKET_NAME,
            key=s3_key,
            content_type="application/zip",
        )
        if timeline:
            timeline_repo.set_regeneration_flags(
                complaint.complaint_id, need_evidence_collection=False
            )
            db.commit()
        return zip_bytes, s3_key

    def get_download_zip_presigned_url(
        self, complaint: Complaint, db: Session, expires_in: int = 3600
    ) -> str:
        """
        다운로드 ZIP(대조 증거 모음 + 타임라인 PDF) 생성 후 presigned URL 반환.
        """
        _, s3_key = self.create_download_zip(complaint=complaint, db=db)
        return generate_presigned_get_url(
            bucket=settings.S3_BUCKET_NAME,
            key=s3_key,
            expires_in=expires_in,
        )


timeline_download_service = TimelineDownloadService()
