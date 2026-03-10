from copy import deepcopy
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.evidence.constant import (
    EVIDENCE_VICTIM_VIDEO_RESTRICT,
    EVIDENCE_VOICE_AUDIO_RESTRICT,
    EVIDENCE_VOICE_IMAGE_RESTRICT,
    EvidenceType,
    EvidenceVariant,
)
from app.domain.evidence_message.repos.evidence_message_repository import (
    EvidenceMessageRepository,
)
from app.domain.evidence_message.service import evidence_message_service
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
from app.domain.timeline.repos import TimelineEvidenceRepository, TimelineRepository


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
            evidence_repo.create(
                TimelineEvidence(
                    timeline_id=timeline.id,
                    evidence_id=ev["evidence_id"],
                    index=ev["index"],
                    original_id=ev["original_id"],
                    type=ev["type"] if isinstance(ev["type"], str) else ev["type"].value,
                )
            )
        db.commit()
        db.refresh(timeline)
        return timeline

    def _resolve_thumbnail_url(
        self,
        evidence_id: UUID,
        timeline_id: UUID,
        db: Session,
    ) -> str:
        """
        has_thumbnail=True인 evidence의 썸네일 URL 생성.
        우선순위: MESSAGE > VICTIM > VOICE
        - MESSAGE, VICTIM: thumbnail s3 key 사용
        - VOICE: thumbnail 미생성 → original 사용 (content_type 이미지인 것, index 최소)
        """
        evidence_repo = TimelineEvidenceRepository(db)
        message_repo = EvidenceMessageRepository(db)
        victim_repo = EvidenceVictimRepository(db)
        voice_repo = EvidenceVoiceRepository(db)

        rows = evidence_repo.list_by_evidence_id(timeline_id, evidence_id)
        if not rows:
            return ""

        # MESSAGE 우선 (s3 detail 사용, JSON 키는 thumbnail_url)
        for row in rows:
            if row.type == EvidenceType.MESSAGE.value:
                msg = message_repo.get(row.original_id)
                if msg:
                    base = msg.s3_key.rsplit("/", 1)[0]
                    s3_key = f"{base}/{EvidenceVariant.DETAIL.value}"
                    return evidence_message_service._get_presigned_url(
                        s3_key=s3_key,
                        expires_in=60 * 60,
                    )

        # VICTIM (s3 detail 사용, JSON 키는 thumbnail_url)
        for row in rows:
            if row.type == EvidenceType.VICTIM.value:
                victim = victim_repo.get(row.original_id)
                if victim:
                    base = victim.s3_key.rsplit("/", 1)[0]
                    s3_key = f"{base}/{EvidenceVariant.DETAIL.value}"
                    return evidence_message_service._get_presigned_url(
                        s3_key=s3_key,
                        expires_in=60 * 60,
                    )

        # VOICE: content_type 이미지인 것 → detail 사용 (message/victim과 동일)
        for row in rows:
            if row.type == EvidenceType.VOICE.value:
                voice = voice_repo.get(row.original_id)
                if voice and voice.content_type in EVIDENCE_VOICE_IMAGE_RESTRICT.allowed_types:
                    base = voice.s3_key.rsplit("/", 1)[0]
                    s3_key = f"{base}/{EvidenceVariant.DETAIL.value}"
                    return evidence_message_service._get_presigned_url(
                        s3_key=s3_key,
                        expires_in=60 * 60,
                    )

        return ""

    def _resolve_has_thumbnail(
        self,
        evidence_id: UUID,
        timeline_id: UUID,
        db: Session,
    ) -> bool:
        """MESSAGE, VICTIM, VOICE(image) 중 하나라도 있으면 True."""
        evidence_repo = TimelineEvidenceRepository(db)
        message_repo = EvidenceMessageRepository(db)
        victim_repo = EvidenceVictimRepository(db)
        voice_repo = EvidenceVoiceRepository(db)

        rows = evidence_repo.list_by_evidence_id(timeline_id, evidence_id)
        for row in rows:
            if row.type == EvidenceType.MESSAGE.value:
                if message_repo.get(row.original_id):
                    return True
        for row in rows:
            if row.type == EvidenceType.VICTIM.value:
                if victim_repo.get(row.original_id):
                    return True
        for row in rows:
            if row.type == EvidenceType.VOICE.value:
                voice = voice_repo.get(row.original_id)
                if voice and voice.content_type in EVIDENCE_VOICE_IMAGE_RESTRICT.allowed_types:
                    return True
        return False

    def _resolve_duration_seconds(
        self,
        evidence_id: UUID,
        timeline_id: UUID,
        has_thumbnail: bool,
        db: Session,
    ) -> int | None:
        """
        duration_seconds는 썸네일 소스가 video/audio일 때만.
        - has_thumbnail True + 썸네일이 VICTIM(video) → victim duration
        - has_thumbnail False + VOICE(audio) 있음 → voice duration
        - 썸네일이 MESSAGE/VICTIM(image)/VOICE(image)면 → None
        """
        evidence_repo = TimelineEvidenceRepository(db)
        message_repo = EvidenceMessageRepository(db)
        victim_repo = EvidenceVictimRepository(db)
        voice_repo = EvidenceVoiceRepository(db)

        rows = evidence_repo.list_by_evidence_id(timeline_id, evidence_id)
        if not rows:
            return None

        # 썸네일 소스와 동일한 우선순위로 확인
        for row in rows:
            if row.type == EvidenceType.MESSAGE.value:
                if message_repo.get(row.original_id):
                    return None  # 썸네일=이미지 → duration 없음
        for row in rows:
            if row.type == EvidenceType.VICTIM.value:
                victim = victim_repo.get(row.original_id)
                if victim:
                    if victim.content_type in EVIDENCE_VICTIM_VIDEO_RESTRICT.allowed_types:
                        return victim.duration_seconds
                    return None  # 썸네일=이미지 → duration 없음
        for row in rows:
            if row.type == EvidenceType.VOICE.value:
                voice = voice_repo.get(row.original_id)
                if voice and voice.content_type in EVIDENCE_VOICE_IMAGE_RESTRICT.allowed_types:
                    return None  # 썸네일=이미지 → duration 없음

        # has_thumbnail False인 경우: VOICE(audio)만 있으면 duration
        if not has_thumbnail:
            durations: list[int] = []
            for row in rows:
                if row.type == EvidenceType.VOICE.value:
                    voice = voice_repo.get(row.original_id)
                    if voice and voice.content_type in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types:
                        if voice.duration_seconds is not None:
                            durations.append(voice.duration_seconds)
            return max(durations) if durations else None

        return None

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
                    ev_id = ev.get("id")
                    if ev_id:
                        try:
                            eid = UUID(ev_id) if isinstance(ev_id, str) else ev_id
                            has_thumbnail = self._resolve_has_thumbnail(
                                evidence_id=eid,
                                timeline_id=timeline.id,
                                db=db,
                            )
                            ev["has_thumbnail"] = has_thumbnail
                            if has_thumbnail:
                                ev["thumbnail_url"] = self._resolve_thumbnail_url(
                                    evidence_id=eid,
                                    timeline_id=timeline.id,
                                    db=db,
                                )
                            duration = self._resolve_duration_seconds(
                                evidence_id=eid,
                                timeline_id=timeline.id,
                                has_thumbnail=has_thumbnail,
                                db=db,
                            )
                            if duration is not None:
                                ev["duration_seconds"] = duration
                        except (ValueError, TypeError):
                            ev["has_thumbnail"] = False
                            ev["thumbnail_url"] = ""

        return schemas.TimelineResponse.model_validate(data)


timeline_service = TimelineService()
