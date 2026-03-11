from copy import deepcopy
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.evidence.constant import (
    EVIDENCE_VICTIM_VIDEO_RESTRICT,
    EVIDENCE_VOICE_AUDIO_RESTRICT,
    EVIDENCE_VOICE_IMAGE_RESTRICT,
    EvidenceType,
    EvidenceVariant,
    FileType,
    get_file_type_from_content_type,
)
from app.domain.evidence.service import evidence_type_service
from app.domain.evidence_message.repos.evidence_message_repository import (
    EvidenceMessageRepository,
)
from app.domain.evidence_victim.repos.evidence_victim_repository import (
    EvidenceVictimRepository,
)
from app.domain.evidence_voice.repos.evidence_voice_repository import (
    EvidenceVoiceRepository,
)
from app.domain.timeline import schemas
from app.domain.timeline.constant import SEED_COMPLAINT_ID
from app.domain.timeline.default_data import (
    DEFAULT_TIMELINE_EVIDENCES,
    DEFAULT_TIMELINE_JSON,
)
from app.domain.timeline.models import Timeline, TimelineEvidence
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
    """타임라인 조회 및 default 데이터 insert."""

    def _insert_dummy_default_data(self, complaint_id: UUID, db: Session) -> Timeline:
        """complaint_id에 해당하는 timeline row 없을 때 default JSON + evidences insert."""
        timeline_repo = TimelineRepository(db)
        evidence_repo = TimelineEvidenceRepository(db)

        timeline = Timeline(
            complaint_id=complaint_id,
            timeline_json=DEFAULT_TIMELINE_JSON,
        )
        timeline_repo.create(timeline)
        db.flush()

        for ev in DEFAULT_TIMELINE_EVIDENCES:
            ev_type = ev.get("evidence_type")
            file_type_val = ev["file_type"]
            evidence_repo.create(
                TimelineEvidence(
                    timeline_id=timeline.id,
                    timeline_evidence_id=ev["timeline_evidence_id"],
                    index=ev["index"],
                    evidence_id=ev.get("evidence_id"),
                    manual_evidence_id=ev.get("manual_evidence_id"),
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
    ) -> _EvidenceMetadata:
        """
        has_thumbnail, thumbnail_url, duration_seconds를 한 번에 조회.
        - is_original_evidence: evidence_type(MESSAGE, VICTIM, VOICE)으로 분기
        - !is_original_evidence: file_type(IMAGE, AUDIO, VIDEO, DOCUMENT)으로 분기 (manual은 evidence_type 없음)
        """
        evidence_repo = TimelineEvidenceRepository(db)
        message_repo = EvidenceMessageRepository(db)
        victim_repo = EvidenceVictimRepository(db)
        voice_repo = EvidenceVoiceRepository(db)
        manual_repo = TimelineManualEvidenceRepository(db)

        rows = evidence_repo.list_by_timeline_evidence_id(timeline_id, timeline_evidence_id)
        if not rows:
            return _EvidenceMetadata(has_thumbnail=False, thumbnail_url="", duration_seconds=None)

        def _get_entity(row: TimelineEvidence):
            if row.is_original_evidence:
                if row.evidence_type == EvidenceType.MESSAGE.value:
                    return message_repo.get(row.evidence_id)
                if row.evidence_type == EvidenceType.VICTIM.value:
                    return victim_repo.get(row.evidence_id)
                if row.evidence_type == EvidenceType.VOICE.value:
                    return voice_repo.get(row.evidence_id)
                return None
            return manual_repo.get(row.manual_evidence_id) if row.manual_evidence_id else None

        def _detail_presigned_url(s3_key: str) -> str:
            base = s3_key.rsplit("/", 1)[0]
            return evidence_type_service._get_presigned_url(
                s3_key=f"{base}/{EvidenceVariant.DETAIL.value}",
                expires_in=60 * 60,
            )

        # original 먼저 (evidence_type 우선순위), manual 나중에
        evidence_type_priority = {
            EvidenceType.MESSAGE.value: 0,
            EvidenceType.VICTIM.value: 1,
            EvidenceType.VOICE.value: 2,
        }
        original_rows = sorted(
            [
                r
                for r in rows
                if r.is_original_evidence and r.evidence_type in evidence_type_priority
            ],
            key=lambda r: evidence_type_priority[r.evidence_type],
        )
        manual_rows = [r for r in rows if not r.is_original_evidence]

        voice_audio_durations: list[int] = []

        for row in original_rows:
            entity = _get_entity(row)
            if entity is None:
                continue
            if row.evidence_type == EvidenceType.MESSAGE.value:
                return _EvidenceMetadata(
                    has_thumbnail=True,
                    thumbnail_url=_detail_presigned_url(entity.s3_key),
                    duration_seconds=None,
                )
            if row.evidence_type == EvidenceType.VICTIM.value:
                dur = (
                    entity.duration_seconds
                    if entity.content_type in EVIDENCE_VICTIM_VIDEO_RESTRICT.allowed_types
                    else None
                )
                return _EvidenceMetadata(
                    has_thumbnail=True,
                    thumbnail_url=_detail_presigned_url(entity.s3_key),
                    duration_seconds=dur,
                )
            if row.evidence_type == EvidenceType.VOICE.value:
                if entity.content_type in EVIDENCE_VOICE_IMAGE_RESTRICT.allowed_types:
                    return _EvidenceMetadata(
                        has_thumbnail=True,
                        thumbnail_url=_detail_presigned_url(entity.s3_key),
                        duration_seconds=None,
                    )
                if (
                    entity.content_type in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types
                    and entity.duration_seconds
                ):
                    voice_audio_durations.append(entity.duration_seconds)

        for row in manual_rows:
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
                    thumbnail_url=_detail_presigned_url(entity.s3_key),
                    duration_seconds=None,
                )
            if ft == FileType.VIDEO:
                return _EvidenceMetadata(
                    has_thumbnail=True,
                    thumbnail_url=_detail_presigned_url(entity.s3_key),
                    duration_seconds=entity.duration_seconds,
                )
            if ft == FileType.AUDIO and entity.duration_seconds:
                voice_audio_durations.append(entity.duration_seconds)

        if voice_audio_durations:
            return _EvidenceMetadata(
                has_thumbnail=False,
                thumbnail_url="",
                duration_seconds=max(voice_audio_durations),
            )
        return _EvidenceMetadata(has_thumbnail=False, thumbnail_url="", duration_seconds=None)

    def get_timeline(self, complaint_id: UUID, db: Session) -> schemas.TimelineResponse:
        """타임라인 조회. row 없으면 default insert 후 반환. thumbnail_url 채움."""
        # TODO: AI 연결 전까지 시드 데이터로 조회
        complaint_id = SEED_COMPLAINT_ID

        timeline_repo = TimelineRepository(db)
        timeline = timeline_repo.get_by_complaint_id(complaint_id)
        if timeline is None:
            timeline = self._insert_dummy_default_data(complaint_id, db)

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
                            )
                            ev["has_thumbnail"] = meta.has_thumbnail
                            ev["thumbnail_url"] = meta.thumbnail_url
                            if meta.duration_seconds is not None:
                                ev["duration_seconds"] = meta.duration_seconds
                        except (ValueError, TypeError):
                            ev["has_thumbnail"] = False
                            ev["thumbnail_url"] = ""

        return schemas.TimelineResponse.model_validate(data)


timeline_service = TimelineService()
