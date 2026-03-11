from uuid import UUID

from sqlalchemy import Integer, cast, func, or_, select, true
from sqlalchemy.orm.attributes import flag_modified

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

    def update_evidence_json(
        self, complaint_id: UUID, timeline_evidence_id: UUID, updates: dict
    ) -> None:
        """timeline_json에서 timeline_evidence_id에 해당하는 객체 수정. date/time 변경 시 슬롯 이동, 동일 시각 있으면 index=max+1."""
        if not updates:
            return
        timeline = self.get_by_complaint_id(complaint_id)
        if not timeline:
            return
        items = timeline.timeline_json.setdefault("items", [])
        ev_id_str = str(timeline_evidence_id)

        found_ev = None
        old_date = old_time = ""
        old_dg = old_evt = None
        old_ev_idx = -1

        for dg in items:
            for evt in dg.get("events", []):
                evidences = evt.get("evidences", [])
                for i, ev in enumerate(evidences):
                    eid = ev.get("timeline_evidence_id") or ev.get("id")
                    if eid and str(eid) == ev_id_str:
                        found_ev = ev
                        old_date = dg.get("date", "")
                        old_time = evt.get("time", "")
                        old_dg, old_evt, old_ev_idx = dg, evt, i
                        break
                if found_ev:
                    break
            if found_ev:
                break

        if not found_ev:
            return

        new_date = updates.get("date", old_date) or old_date
        new_time = updates.get("time", old_time) or old_time

        for k, v in updates.items():
            if v is not None:
                found_ev[k] = v

        if (new_date, new_time) != (old_date, old_time):
            evidences = old_evt["evidences"]
            evidences.pop(old_ev_idx)
            if not evidences:
                old_dg["events"].remove(old_evt)
            if not old_dg["events"]:
                items.remove(old_dg)

            target_evidences = None
            for dg in items:
                if dg.get("date") != new_date:
                    continue
                for evt in dg.get("events", []):
                    if evt.get("time") == new_time:
                        target_evidences = evt.setdefault("evidences", [])
                        break
                if target_evidences is not None:
                    break
                dg.setdefault("events", []).append({"time": new_time, "evidences": []})
                target_evidences = dg["events"][-1]["evidences"]
                break

            if target_evidences is None:
                items.append({"date": new_date, "events": [{"time": new_time, "evidences": []}]})
                target_evidences = items[-1]["events"][0]["evidences"]

            found_ev["index"] = max((e.get("index", 1) for e in target_evidences), default=0) + 1
            target_evidences.append(found_ev)

        timeline.timeline_json["items"] = [dg for dg in items if dg.get("events")]
        flag_modified(timeline, "timeline_json")


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
