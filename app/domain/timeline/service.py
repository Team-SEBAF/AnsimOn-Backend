from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import dataclass
from io import BytesIO
from uuid import UUID

from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.aws import delete_s3_by_prefixes, download_s3_object, upload_fileobj
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence.constant import (
    EVIDENCE_IMAGE_RESTRICT,
    EVIDENCE_VIDEO_RESTRICT,
    EVIDENCE_VOICE_AUDIO_RESTRICT,
    EvidenceType,
    EvidenceVariant,
    FileType,
    get_file_type_from_content_type,
)
from app.domain.evidence.errors.register_validation_error import (
    raise_evidence_register_validation_failed,
)
from app.domain.evidence.service import evidence_type_service
from app.domain.evidence.utils import (
    collect_register_failures_from_metadata,
    fetch_s3_metadata_for_register,
    generate_presigned_urls_for_unrestricted_content,
    get_restrict_by_content_type,
)
from app.domain.evidence_incident_log.models.evidence_incident_log_model import (
    EvidenceIncidentLogType,
)
from app.domain.evidence_incident_log.repos.evidence_incident_log_repository import (
    EvidenceIncidentLogFileRepository,
    EvidenceIncidentLogRepository,
)
from app.domain.evidence_message.repos.evidence_message_repository import (
    EvidenceMessageRepository,
)
from app.domain.evidence_message.utils import make_image_top_crop
from app.domain.evidence_report_record.repos.evidence_report_record_repository import (
    EvidenceReportRecordRepository,
)
from app.domain.evidence_victim.repos.evidence_victim_repository import (
    EvidenceVictimRepository,
)
from app.domain.evidence_victim.utils import get_video_duration, get_video_image_at_0
from app.domain.evidence_voice.repos.evidence_voice_repository import (
    EvidenceVoiceRepository,
)
from app.domain.evidence_voice.utils import get_audio_duration
from app.domain.timeline import schemas
from app.domain.timeline.constant import TimelineTag
from app.domain.timeline.default_data import (
    DEFAULT_TIMELINE_EVIDENCES,
    DEFAULT_TIMELINE_JSON,
)
from app.domain.timeline.errors import (
    GetTimelineErrorCode,
    TimelineManualEvidenceNotAllowedErrorCode,
)
from app.domain.timeline.models import Timeline, TimelineEvidence, TimelineManualEvidence
from app.domain.timeline.repos import (
    TimelineEvidenceRepository,
    TimelineManualEvidenceRepository,
    TimelineRepository,
)


@dataclass
class _EvidenceMetadata:
    has_thumbnail: bool
    thumbnail_url: str
    duration_seconds: int | None


class TimelineService:
    @staticmethod
    def _detail_presigned_url(s3_key: str) -> str:
        """s3_key의 detail variant presigned URL 반환."""
        base = s3_key.rsplit("/", 1)[0]
        return evidence_type_service._get_presigned_url(
            s3_key=f"{base}/{EvidenceVariant.DETAIL.value}",
            expires_in=60 * 60,
        )

    def _insert_dummy_default_data(self, complaint_id: UUID, db: Session) -> Timeline:
        """complaint_id에 해당하는 timeline row 없을 때 default JSON + evidences insert."""
        timeline_repo = TimelineRepository(db)
        timeline_evidence_repo = TimelineEvidenceRepository(db)

        timeline = Timeline(
            complaint_id=complaint_id,
            timeline_json=DEFAULT_TIMELINE_JSON,
        )
        timeline_repo.create(timeline)
        db.flush()

        for ev in DEFAULT_TIMELINE_EVIDENCES:
            ev_type = ev.get("evidence_type")
            file_type_val = ev["file_type"]
            timeline_evidence_repo.create(
                TimelineEvidence(
                    timeline_id=timeline.id,
                    timeline_evidence_id=ev["timeline_evidence_id"],
                    index=ev["index"],
                    referenced_evidence_id=ev.get("referenced_evidence_id"),
                    referenced_manual_evidence_id=ev.get("referenced_manual_evidence_id"),
                    is_original_evidence=ev.get("is_original_evidence", True),
                    evidence_type=ev_type.value
                    if ev_type and hasattr(ev_type, "value")
                    else ev_type,
                    file_type=file_type_val.value
                    if hasattr(file_type_val, "value")
                    else file_type_val,
                )
            )
        db.commit()
        db.refresh(timeline)
        return timeline

    def _resolve_evidence_metadata(
        self,
        timeline_evidence_id: UUID,
        timeline_id: UUID,
        db: Session,
        is_ai_original: bool = True,
    ) -> _EvidenceMetadata:
        """
        has_thumbnail, thumbnail_url, duration_seconds를 한 번에 조회.
        - is_ai_original=True: original(evidence_*) rows만 처리
        - is_ai_original=False: manual rows만 처리
        - 그룹은 항상 이미지 타입, index 순 첫 번째 이미지/비디오를 썸네일로 사용.
        """
        timeline_evidence_repo = TimelineEvidenceRepository(db)
        message_repo = EvidenceMessageRepository(db)
        victim_repo = EvidenceVictimRepository(db)
        voice_repo = EvidenceVoiceRepository(db)
        manual_repo = TimelineManualEvidenceRepository(db)

        rows = timeline_evidence_repo.list_by_timeline_evidence_id(
            timeline_id, timeline_evidence_id
        )
        if not rows:
            return _EvidenceMetadata(has_thumbnail=False, thumbnail_url="", duration_seconds=None)

        def _get_entity(row: TimelineEvidence):
            if row.is_original_evidence:
                if row.evidence_type == EvidenceType.MESSAGE.value:
                    return message_repo.get(row.referenced_evidence_id)
                if row.evidence_type == EvidenceType.VICTIM.value:
                    return victim_repo.get(row.referenced_evidence_id)
                if row.evidence_type == EvidenceType.VOICE.value:
                    return voice_repo.get(row.referenced_evidence_id)
                return None
            return (
                manual_repo.get(row.referenced_manual_evidence_id)
                if row.referenced_manual_evidence_id
                else None
            )

        # is_ai_original에 따라 처리할 rows 선택 (index 순)
        if is_ai_original:
            target_rows = [r for r in rows if r.is_original_evidence]
        else:
            target_rows = [r for r in rows if not r.is_original_evidence]

        voice_audio_durations: list[int] = []

        for row in target_rows:
            entity = _get_entity(row)
            if entity is None:
                continue
            ft = (
                FileType(row.file_type)
                if row.file_type
                else get_file_type_from_content_type(entity.content_type)
            )
            if ft == FileType.IMAGE:
                return _EvidenceMetadata(
                    has_thumbnail=True,
                    thumbnail_url=self._detail_presigned_url(entity.s3_key),
                    duration_seconds=None,
                )
            if ft == FileType.VIDEO:
                dur = entity.duration_seconds
                return _EvidenceMetadata(
                    has_thumbnail=True,
                    thumbnail_url=self._detail_presigned_url(entity.s3_key),
                    duration_seconds=dur,
                )
            if ft == FileType.AUDIO:
                dur = entity.duration_seconds
                if dur:
                    voice_audio_durations.append(dur)

        if voice_audio_durations:
            return _EvidenceMetadata(
                has_thumbnail=False,
                thumbnail_url="",
                duration_seconds=sum(voice_audio_durations),
            )
        return _EvidenceMetadata(has_thumbnail=False, thumbnail_url="", duration_seconds=None)

    def _ensure_timeline_evidence_is_manual(
        self,
        complaint_id: UUID,
        timeline_evidence_id: UUID,
        db: Session,
    ) -> None:
        """
        timeline_evidence_id가 직접 추가 증거(is_ai_original=False)인지 검사.
        AI 분석 증거(is_ai_original=True)에는 Presigned URL/Register 사용 불가 → CodeException raise.
        """
        timeline_repo = TimelineRepository(db)
        ev_meta = timeline_repo.get_evidence_metadata_from_json(complaint_id, timeline_evidence_id)
        if ev_meta is None:
            raise CodeException(
                code=GetTimelineErrorCode.TIMELINE_EVIDENCE_NOT_FOUND,
                message="타임라인 증거를 찾을 수 없습니다.",
                debug_message=f"timeline_evidence_id: {timeline_evidence_id}에 해당하는 증거가 timeline_json에 없습니다.",
                status_code=404,
            )
        is_ai_original = ev_meta.get("is_ai_original", True)
        if is_ai_original:
            raise CodeException(
                code=TimelineManualEvidenceNotAllowedErrorCode.TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED,
                message="타임라인 증거 타입이 불일치한 작업을 시도했습니다.",
                debug_message=f"timeline_evidence_id: {timeline_evidence_id}에 해당하는 증거가 AI 분석 증거(is_ai_original=True)입니다. 직접 추가 증거에만 사용 가능합니다.",
                status_code=400,
            )

    def get_timeline(
        self, complaint_id: UUID, db: Session, *, generate_dummy: bool = False
    ) -> schemas.TimelineResponse:
        """타임라인 조회. generate_dummy=True일 때만 시드 삽입(기존 row 있으면 삭제 후)."""
        timeline_repo = TimelineRepository(db)
        timeline = timeline_repo.get_by_complaint_id(complaint_id)

        if generate_dummy:
            if timeline is not None:
                timeline_repo.delete(timeline)
                db.flush()
            timeline = self._insert_dummy_default_data(complaint_id, db)
        elif timeline is None:
            raise CodeException(
                code=GetTimelineErrorCode.TIMELINE_NOT_FOUND,
                message="타임라인을 찾을 수 없습니다.",
                debug_message=f"complaint_id: {complaint_id}에 해당하는 타임라인이 없습니다.",
                status_code=404,
            )

        data = deepcopy(timeline.timeline_json)

        for date_group in data.get("items", []):
            for event in date_group.get("events", []):
                for ev in event.get("evidences", []):
                    ev_id = ev.get("timeline_evidence_id") or ev.get("id")
                    if ev_id:
                        try:
                            eid = UUID(ev_id) if isinstance(ev_id, str) else ev_id
                            meta = self._resolve_evidence_metadata(
                                timeline_evidence_id=eid,
                                timeline_id=timeline.id,
                                db=db,
                                is_ai_original=ev.get("is_ai_original", True),
                            )
                            ev["has_thumbnail"] = meta.has_thumbnail
                            ev["thumbnail_url"] = meta.thumbnail_url
                            if meta.duration_seconds is not None:
                                ev["duration_seconds"] = meta.duration_seconds
                        except (ValueError, TypeError):
                            ev["has_thumbnail"] = False
                            ev["thumbnail_url"] = ""

        return schemas.TimelineResponse.model_validate(data)

    def get_timeline_evidences(
        self,
        complaint_id: UUID,
        timeline_evidence_id: UUID,
        db: Session,
    ) -> schemas.TimelineEvidenceDetailResponse:
        """timeline_evidence_id에 해당하는 타임라인 증거 메타데이터 + 증거 목록 조회."""
        timeline_repo = TimelineRepository(db)
        timeline_evidence_repo = TimelineEvidenceRepository(db)

        timeline_id = timeline_repo.get_id_by_complaint_id(complaint_id)

        ev_meta = timeline_repo.get_evidence_metadata_from_json(complaint_id, timeline_evidence_id)
        if ev_meta is None:
            raise CodeException(
                code=GetTimelineErrorCode.TIMELINE_EVIDENCE_NOT_FOUND,
                message="타임라인 증거를 찾을 수 없습니다.",
                debug_message=f"timeline_evidence_id: {timeline_evidence_id}에 해당하는 증거가 timeline_json에 없습니다.",
                status_code=404,
            )

        is_ai_original = ev_meta.get("is_ai_original", True)

        rows = timeline_evidence_repo.list_by_timeline_evidence_id(
            timeline_id, timeline_evidence_id
        )

        base_response = {
            "timeline_evidence_id": timeline_evidence_id,
            "index": ev_meta.get("index", 1),
            "date": ev_meta.get("date", ""),
            "time": ev_meta.get("time", ""),
            "title": ev_meta.get("title", ""),
            "description": ev_meta.get("description", ""),
            "tags": ev_meta.get("tags", []),
            "referenced_evidence_count": ev_meta.get("referenced_evidence_count", 0),
            "is_ai_original": is_ai_original,
        }

        if not rows:
            return schemas.TimelineEvidenceDetailResponse(**base_response, evidences=[])

        def _to_item(
            referenced_id: UUID,
            filename: str,
            size_bytes: int | None,
            s3_key: str | None,
            content_type: str | None,
            duration_seconds: int | None,
            evidence_type: str | None,
            file_type: str,
        ) -> schemas.TimelineEvidenceItem:
            ft = (
                FileType(file_type)
                if file_type
                else (
                    get_file_type_from_content_type(content_type) if content_type else FileType.ETC
                )
            )
            thumb = (
                self._detail_presigned_url(s3_key)
                if s3_key and ft in (FileType.IMAGE, FileType.VIDEO)
                else ""
            )
            dur = duration_seconds if ft in (FileType.VIDEO, FileType.AUDIO) else None
            return schemas.TimelineEvidenceItem(
                referenced_id=referenced_id,
                filename=filename,
                size_bytes=size_bytes,
                thumbnail_url=thumb,
                duration_seconds=dur,
                evidence_type=evidence_type,
                file_type=ft.value,
            )

        evidence_items: list[schemas.TimelineEvidenceItem] = []

        if is_ai_original:
            message_repo = EvidenceMessageRepository(db)
            victim_repo = EvidenceVictimRepository(db)
            voice_repo = EvidenceVoiceRepository(db)
            report_record_repo = EvidenceReportRecordRepository(db)
            incident_log_repo = EvidenceIncidentLogRepository(db)
            incident_log_file_repo = EvidenceIncidentLogFileRepository(db)
            for row in rows:
                if row.evidence_type == EvidenceType.MESSAGE.value:
                    entity = message_repo.get(row.referenced_evidence_id)
                    if entity:
                        evidence_items.append(
                            _to_item(
                                entity.message_id,
                                entity.filename,
                                entity.size_bytes,
                                entity.s3_key,
                                entity.content_type,
                                None,
                                row.evidence_type,
                                row.file_type,
                            )
                        )
                elif row.evidence_type == EvidenceType.VICTIM.value:
                    entity = victim_repo.get(row.referenced_evidence_id)
                    if entity:
                        evidence_items.append(
                            _to_item(
                                entity.victim_id,
                                entity.filename,
                                entity.size_bytes,
                                entity.s3_key,
                                entity.content_type,
                                entity.duration_seconds,
                                row.evidence_type,
                                row.file_type,
                            )
                        )
                elif row.evidence_type == EvidenceType.VOICE.value:
                    entity = voice_repo.get(row.referenced_evidence_id)
                    if entity:
                        evidence_items.append(
                            _to_item(
                                entity.voice_id,
                                entity.filename,
                                entity.size_bytes,
                                entity.s3_key,
                                entity.content_type,
                                entity.duration_seconds,
                                row.evidence_type,
                                row.file_type,
                            )
                        )
                elif row.evidence_type == EvidenceType.REPORT_RECORD.value:
                    entity = report_record_repo.get(row.referenced_evidence_id)
                    if entity:
                        evidence_items.append(
                            _to_item(
                                entity.report_record_id,
                                entity.filename,
                                entity.size_bytes,
                                entity.s3_key,
                                entity.content_type,
                                None,
                                row.evidence_type,
                                row.file_type,
                            )
                        )
                elif row.evidence_type == EvidenceType.INCIDENT_LOG.value:
                    log = incident_log_repo.get(row.referenced_evidence_id)
                    if not log:
                        continue
                    if log.type == EvidenceIncidentLogType.FILE:
                        f = incident_log_file_repo.get(log.incident_log_id)
                        if f:
                            evidence_items.append(
                                _to_item(
                                    log.incident_log_id,
                                    log.name,
                                    f.size_bytes,
                                    f.s3_key,
                                    f.content_type,
                                    None,
                                    row.evidence_type,
                                    FileType.DOCUMENT.value,
                                )
                            )
                    elif log.type == EvidenceIncidentLogType.FORM_DATA:
                        evidence_items.append(
                            _to_item(
                                log.incident_log_id,
                                log.name,
                                None,
                                None,
                                None,
                                None,
                                row.evidence_type,
                                FileType.DOCUMENT.value,
                            )
                        )
        else:
            manual_repo = TimelineManualEvidenceRepository(db)
            manual_entities = {
                e.id: e
                for e in manual_repo.list_by_timeline_evidence_id(timeline_id, timeline_evidence_id)
            }
            for row in rows:
                entity = manual_entities.get(row.referenced_manual_evidence_id)
                if entity:
                    evidence_items.append(
                        _to_item(
                            entity.id,
                            entity.filename,
                            entity.size_bytes,
                            entity.s3_key,
                            entity.content_type,
                            entity.duration_seconds,
                            None,
                            row.file_type,
                        )
                    )

        return schemas.TimelineEvidenceDetailResponse(
            **base_response,
            evidences=evidence_items,
        )

    def update_timeline_evidence_form_data(
        self,
        complaint_id: UUID,
        timeline_evidence_id: UUID,
        request: schemas.UpdateTimelineEvidenceRequest,
        db: Session,
    ) -> schemas.TimelineEvidenceMetadataResponse:
        """타임라인 증거 메타데이터 수정. req body 키에 대해서만 JSON 값 수정. (증거 수정, 삭제 X)"""
        timeline_repo = TimelineRepository(db)
        updates = request.model_dump(exclude_unset=True, mode="json")
        timeline_repo.update_evidence_json(complaint_id, timeline_evidence_id, updates)
        db.commit()

        ev_meta = timeline_repo.get_evidence_metadata_from_json(complaint_id, timeline_evidence_id)
        ev_meta = ev_meta or {}
        response_data = {
            "timeline_evidence_id": timeline_evidence_id,
            **ev_meta,
            "tags": [TimelineTag(t) if isinstance(t, str) else t for t in ev_meta.get("tags", [])],
        }
        return schemas.TimelineEvidenceMetadataResponse(**response_data)

    def delete_timeline_evidences(
        self,
        complaint: Complaint,
        timeline_evidence_ids: list[UUID],
        db: Session,
    ) -> None:
        for timeline_evidence_id in timeline_evidence_ids:
            self._delete_timeline_evidence_one(
                complaint=complaint,
                timeline_evidence_id=timeline_evidence_id,
                db=db,
            )
        timeline_repo = TimelineRepository(db)
        timeline_repo.set_regeneration_flags(
            complaint.complaint_id, need_evidence_collection_regeneration=True
        )
        db.commit()

    def _delete_timeline_evidence_one(
        self,
        complaint: Complaint,
        timeline_evidence_id: UUID,
        db: Session,
    ) -> None:
        timeline_repo = TimelineRepository(db)
        timeline_id = timeline_repo.get_id_by_complaint_id(complaint.complaint_id)
        timeline_evidence_repo = TimelineEvidenceRepository(db)

        rows = timeline_evidence_repo.list_by_timeline_evidence_id(
            timeline_id, timeline_evidence_id
        )
        manual_ids = [
            r.referenced_manual_evidence_id
            for r in rows
            if not r.is_original_evidence and r.referenced_manual_evidence_id
        ]
        if manual_ids:
            self.delete_referenced_manual_evidences(
                complaint=complaint,
                timeline_evidence_id=timeline_evidence_id,
                referenced_manual_evidence_ids=manual_ids,
                db=db,
            )

        timeline_evidence_repo.delete_by_timeline_evidence_id(timeline_id, timeline_evidence_id)
        timeline_repo.remove_evidence_from_json(complaint.complaint_id, timeline_evidence_id)

    def upload_manual_timeline_evidence_form_data(
        self,
        complaint_id: UUID,
        request: schemas.ManualTimelineEvidenceFormDataUploadRequest,
        db: Session,
    ) -> schemas.ManualTimelineEvidenceFormDataResponse:
        timeline_repo = TimelineRepository(db)
        timeline_evidence_id, index = timeline_repo.add_manual_evidence_to_json(
            complaint_id=complaint_id,
            date=request.date,
            time=request.time,
            title=request.title,
            description=request.description,
            tags=request.tags,
        )
        timeline_repo.set_regeneration_flags(
            complaint_id, need_evidence_collection_regeneration=True
        )
        db.commit()

        return schemas.ManualTimelineEvidenceFormDataResponse(
            timeline_evidence_id=timeline_evidence_id,
            index=index,
            date=request.date,
            time=request.time,
            title=request.title,
            description=request.description,
            tags=request.tags,
        )

    def get_referenced_manual_evidence_presigned_url(
        self,
        complaint: Complaint,
        timeline_evidence_id: UUID,
        request: schemas.ManualTimelineEvidencePresignedRequest,
        db: Session,
    ) -> schemas.ReferencedManualEvidencePresignedResponse:
        self._ensure_timeline_evidence_is_manual(
            complaint_id=complaint.complaint_id,
            timeline_evidence_id=timeline_evidence_id,
            db=db,
        )

        def s3_key_builder(c: Complaint, eid: UUID) -> str:
            return f"{c.user_sub}/complaints/{c.complaint_id}/timeline-referenced-manual-evidences/{timeline_evidence_id}/{eid}/original"

        rows = generate_presigned_urls_for_unrestricted_content(
            complaint=complaint,
            items=request.items,
            s3_key_builder=s3_key_builder,
            id_field_name="referenced_manual_evidence_id",
        )
        return schemas.ReferencedManualEvidencePresignedResponse(
            items=[
                schemas.ReferencedManualEvidencePresignedItem(
                    index=r["index"],
                    filename=r["filename"],
                    url=r["url"],
                    referenced_manual_evidence_id=r["referenced_manual_evidence_id"],
                )
                for r in rows
            ]
        )

    def register_referenced_manual_evidences(
        self,
        complaint: Complaint,
        timeline_evidence_id: UUID,
        request: schemas.ManualTimelineEvidenceRegisterRequest,
        db: Session,
    ) -> schemas.ReferencedManualEvidenceRegisterResponse:
        self._ensure_timeline_evidence_is_manual(
            complaint_id=complaint.complaint_id,
            timeline_evidence_id=timeline_evidence_id,
            db=db,
        )

        path_segment = f"{timeline_evidence_id}"
        metadata_list = fetch_s3_metadata_for_register(
            complaint=complaint,
            items=request.items,
            path_segment=path_segment,
            get_evidence_id=lambda item: item.referenced_manual_evidence_id,
            build_extra=lambda item, s3_key, ct, size: {
                "referenced_manual_evidence_id": item.referenced_manual_evidence_id,
                "timeline_evidence_id": timeline_evidence_id,
                "filename": item.filename,
            },
            path_prefix="timeline-referenced-manual-evidences",
        )

        (
            size_bytes_failed_ids,
            valid_metadata,
        ) = collect_register_failures_from_metadata(metadata_list, "referenced_manual_evidence_id")

        def _process_manual_item(m: dict) -> tuple[dict | None, str | None]:
            ct = m["content_type"]
            r = get_restrict_by_content_type(ct)
            duration_seconds = None
            file_bytes = None
            if ct in EVIDENCE_VIDEO_RESTRICT.allowed_types:
                try:
                    file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
                    duration_seconds = get_video_duration(file_bytes)
                    if r.max_duration_seconds and duration_seconds > r.max_duration_seconds:
                        return None, str(m["referenced_manual_evidence_id"])
                except Exception:
                    return None, str(m["referenced_manual_evidence_id"])
            elif ct in EVIDENCE_IMAGE_RESTRICT.allowed_types:
                duration_seconds = 0
                try:
                    file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
                except Exception:
                    return None, str(m["referenced_manual_evidence_id"])
            elif ct in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types:
                try:
                    file_bytes = download_s3_object(settings.S3_BUCKET_NAME, m["s3_key"])
                    duration_seconds = get_audio_duration(file_bytes)
                    if r.max_duration_seconds and duration_seconds > r.max_duration_seconds:
                        return None, str(m["referenced_manual_evidence_id"])
                except (ValueError, TypeError):
                    return None, str(m["referenced_manual_evidence_id"])
            if file_bytes and ct in (
                EVIDENCE_VIDEO_RESTRICT.allowed_types | EVIDENCE_IMAGE_RESTRICT.allowed_types
            ):
                base_key = m["s3_key"].rsplit("/", 1)[0]
                detail_key = f"{base_key}/detail"
                if ct in EVIDENCE_VIDEO_RESTRICT.allowed_types:
                    detail_bytes, _, _ = get_video_image_at_0(file_bytes, size=400, quality=75)
                else:
                    detail_bytes, _, _ = make_image_top_crop(
                        file_bytes=file_bytes, size=400, quality=75
                    )
                upload_fileobj(
                    fileobj=BytesIO(detail_bytes),
                    bucket=settings.S3_BUCKET_NAME,
                    key=detail_key,
                    content_type="image/jpeg",
                )
            row = {
                "referenced_manual_evidence_id": m["referenced_manual_evidence_id"],
                "timeline_evidence_id": m["timeline_evidence_id"],
                "filename": m["filename"],
                "s3_key": m["s3_key"],
                "content_type": ct,
                "size_bytes": m["size_bytes"],
                "duration_seconds": duration_seconds,
            }
            return row, None

        with ThreadPoolExecutor(max_workers=max(1, min(len(valid_metadata), 5))) as executor:
            results = list(executor.map(_process_manual_item, valid_metadata))
        rows = [r for r, _ in results if r is not None]
        extraction_failed_ids = [eid for _, eid in results if eid is not None]
        duration_seconds_failed_ids: list[str] = []
        for r in rows:
            ct = r.get("content_type", "")
            restrict = get_restrict_by_content_type(ct)
            if restrict.max_duration_seconds is not None:
                dur = r.get("duration_seconds", 0)
                if dur > restrict.max_duration_seconds:
                    duration_seconds_failed_ids.append(str(r["referenced_manual_evidence_id"]))
        duration_total = duration_seconds_failed_ids + extraction_failed_ids
        if size_bytes_failed_ids or duration_total:
            raise_evidence_register_validation_failed(
                content_type_failed_evidence_ids=[],
                size_bytes_failed_evidence_ids=size_bytes_failed_ids,
                duration_seconds_failed_evidence_ids=duration_total if duration_total else [],
            )

        timeline_evidence_repo = TimelineEvidenceRepository(db)
        timeline_repo = TimelineRepository(db)
        timeline = timeline_repo.get_by_complaint_id(complaint.complaint_id)

        existing_rows = timeline_evidence_repo.list_by_timeline_evidence_id(
            timeline.id, timeline_evidence_id
        )
        next_index = max((r.index for r in existing_rows), default=0) + 1

        manual_mappings = [
            {
                "id": r["referenced_manual_evidence_id"],
                "complaint_id": complaint.complaint_id,
                "type": get_file_type_from_content_type(r["content_type"]).value,
                "duration_seconds": r.get("duration_seconds"),
                "filename": r["filename"],
                "s3_key": r["s3_key"],
                "content_type": r["content_type"],
                "size_bytes": r["size_bytes"],
            }
            for r in rows
        ]
        evidence_mappings = [
            {
                "timeline_id": timeline.id,
                "timeline_evidence_id": timeline_evidence_id,
                "index": next_index + i,
                "referenced_manual_evidence_id": r["referenced_manual_evidence_id"],
                "is_original_evidence": False,
                "evidence_type": None,
                "file_type": get_file_type_from_content_type(r["content_type"]).value,
            }
            for i, r in enumerate(rows)
        ]
        db.bulk_insert_mappings(TimelineManualEvidence, manual_mappings)
        db.bulk_insert_mappings(TimelineEvidence, evidence_mappings)

        actual_count = len(
            timeline_evidence_repo.list_by_timeline_evidence_id(timeline.id, timeline_evidence_id)
        )
        timeline_repo.update_referenced_evidence_count(
            complaint.complaint_id, timeline_evidence_id, actual_count
        )
        timeline_repo.set_regeneration_flags(
            complaint.complaint_id, need_evidence_collection_regeneration=True
        )
        db.commit()
        results_resp = [
            schemas.ReferencedManualEvidenceRegisterItem(
                referenced_manual_evidence_id=r["referenced_manual_evidence_id"],
                file_type=get_file_type_from_content_type(r["content_type"]).value,
                filename=r["filename"],
                content_type=r["content_type"],
                size_bytes=r["size_bytes"],
                duration_seconds=r.get("duration_seconds"),
            )
            for r in rows
        ]
        return schemas.ReferencedManualEvidenceRegisterResponse(items=results_resp)

    def delete_referenced_manual_evidences(
        self,
        complaint: Complaint,
        timeline_evidence_id: UUID,
        referenced_manual_evidence_ids: list[UUID],
        db: Session,
    ) -> None:
        self._ensure_timeline_evidence_is_manual(
            complaint_id=complaint.complaint_id,
            timeline_evidence_id=timeline_evidence_id,
            db=db,
        )
        timeline_repo = TimelineRepository(db)
        timeline_id = timeline_repo.get_id_by_complaint_id(complaint.complaint_id)

        timeline_evidence_repo = TimelineEvidenceRepository(db)
        manual_repo = TimelineManualEvidenceRepository(db)

        rows = timeline_evidence_repo.list_by_timeline_evidence_id(
            timeline_id, timeline_evidence_id
        )
        to_delete = [
            r
            for r in rows
            if r.referenced_manual_evidence_id in referenced_manual_evidence_ids
            and not r.is_original_evidence
        ]

        if not to_delete:
            return
        manuals = [
            manual_repo.get(r.referenced_manual_evidence_id)
            for r in to_delete
            if r.referenced_manual_evidence_id
        ]
        manuals = [m for m in manuals if m is not None]

        if manuals:
            prefixes = [m.s3_key.rsplit("/", 1)[0] + "/" for m in manuals]
            delete_s3_by_prefixes(settings.S3_BUCKET_NAME, prefixes)
        for manual in manuals:
            manual_repo.delete(manual)
        db.commit()

        actual_count = len(
            timeline_evidence_repo.list_by_timeline_evidence_id(timeline_id, timeline_evidence_id)
        )
        timeline_repo.update_referenced_evidence_count(
            complaint.complaint_id, timeline_evidence_id, actual_count
        )
        timeline_repo.set_regeneration_flags(
            complaint.complaint_id, need_evidence_collection_regeneration=True
        )
        db.commit()


timeline_service = TimelineService()
