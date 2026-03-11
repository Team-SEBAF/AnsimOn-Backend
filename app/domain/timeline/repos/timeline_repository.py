from uuid import UUID

from sqlalchemy import Integer, cast, func, or_, select, true

from app.base.base_repository import BaseRepository
from app.domain.timeline.models import Timeline, TimelineEvidence, TimelineManualEvidence


class TimelineRepository(BaseRepository):
    model_class = Timeline
    pk_attr = "id"

    def get_by_complaint_id(self, complaint_id: UUID) -> Timeline | None:
        return self.db.query(Timeline).filter(Timeline.complaint_id == complaint_id).first()

    def get_evidence_metadata_from_json(
        self, complaint_id: UUID, timeline_evidence_id: UUID
    ) -> dict | None:
        """
        timeline_json에서 timeline_evidence_id에 해당하는 evidence 메타데이터만 조회.

        timeline_json 구조: items[] -> events[] -> evidences[]
        - items: 날짜별 그룹 (date, events)
        - events: 시각별 그룹 (time, evidences)
        - evidences: 증거 객체 (timeline_evidence_id, index, title, description, tags)

        JSON 배열은 인덱스 직접 접근 불가 → jsonb_array_elements로 각 레벨을 행으로 펼친 뒤
        LATERAL JOIN으로 중첩 탐색. 3단계 중첩이므로 3번의 join 필요.
        """
        ev_id_str = str(timeline_evidence_id)
        dg = func.jsonb_array_elements(Timeline.timeline_json["items"]).table_valued("value")
        evt = func.jsonb_array_elements(dg.c.value.op("->")("events")).table_valued("value")
        ev = func.jsonb_array_elements(evt.c.value.op("->")("evidences")).table_valued("value")

        stmt = (
            select(
                dg.c.value.op("->>")("date").label("date"),
                evt.c.value.op("->>")("time").label("time"),
                cast(ev.c.value.op("->>")("index"), Integer).label("index"),
                ev.c.value.op("->>")("title").label("title"),
                ev.c.value.op("->>")("description").label("description"),
                ev.c.value.op("->")("tags").label("tags"),
            )
            .select_from(Timeline.__table__)
            .join(dg, true())
            .join(evt, true())
            .join(ev, true())
            .where(
                Timeline.complaint_id == complaint_id,
                or_(
                    ev.c.value.op("->>")("timeline_evidence_id") == ev_id_str,
                    ev.c.value.op("->>")("id") == ev_id_str,
                ),
            )
            .limit(1)
        )
        row = self.db.execute(stmt).fetchone()
        if not row:
            return None
        tags = row.tags if isinstance(row.tags, list) else []
        return {
            "date": row.date or "",
            "time": row.time or "",
            "index": row.index or 1,
            "title": row.title or "",
            "description": row.description or "",
            "tags": tags,
        }


class TimelineEvidenceRepository(BaseRepository):
    model_class = TimelineEvidence
    pk_attr = "id"

    def list_by_timeline_id(self, timeline_id: UUID) -> list[TimelineEvidence]:
        return (
            self.db.query(TimelineEvidence)
            .filter(TimelineEvidence.timeline_id == timeline_id)
            .order_by(TimelineEvidence.timeline_evidence_id, TimelineEvidence.index)
            .all()
        )

    def list_by_timeline_evidence_id(
        self, timeline_id: UUID, timeline_evidence_id: UUID
    ) -> list[TimelineEvidence]:
        """timeline_evidence_id(timeline JSON 그룹 id)에 해당하는 timeline_evidences 목록, index 순."""
        return (
            self.db.query(TimelineEvidence)
            .filter(
                TimelineEvidence.timeline_id == timeline_id,
                TimelineEvidence.timeline_evidence_id == timeline_evidence_id,
            )
            .order_by(TimelineEvidence.index)
            .all()
        )


class TimelineManualEvidenceRepository(BaseRepository):
    model_class = TimelineManualEvidence
    pk_attr = "id"

    def list_by_timeline_evidence_id(
        self, timeline_id: UUID, timeline_evidence_id: UUID
    ) -> list[TimelineManualEvidence]:
        """timeline_evidence_id에 해당하는 수동 증거 목록 조회 (N+1 방지)."""
        return (
            self.db.query(TimelineManualEvidence)
            .join(
                TimelineEvidence,
                TimelineManualEvidence.id == TimelineEvidence.manual_evidence_id,
            )
            .filter(
                TimelineEvidence.timeline_id == timeline_id,
                TimelineEvidence.timeline_evidence_id == timeline_evidence_id,
                TimelineEvidence.is_original_evidence.is_(False),
            )
            .order_by(TimelineEvidence.index)
            .all()
        )
