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

    def set_regeneration_flags(
        self,
        complaint_id: UUID,
        *,
        need_evidence_collection_regeneration: bool | None = None,
        need_timeline_pdf_regeneration: bool | None = None,
    ) -> None:
        """다운로드 ZIP(대조 증거 모음/타임라인 PDF) 재생성 필요 플래그 설정."""
        timeline = self.get_by_complaint_id(complaint_id)
        if not timeline:
            return
        if need_evidence_collection_regeneration is not None:
            timeline.need_evidence_collection_regeneration = need_evidence_collection_regeneration
        if need_timeline_pdf_regeneration is not None:
            timeline.need_timeline_pdf_regeneration = need_timeline_pdf_regeneration

    def get_id_by_complaint_id(self, complaint_id: UUID) -> UUID | None:
        row = self.db.query(Timeline.id).filter(Timeline.complaint_id == complaint_id).first()
        return row[0] if row else None

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
                ev.c.value.op("->>")("is_ai_original").label("is_ai_original"),
                cast(ev.c.value.op("->>")("referenced_evidence_count"), Integer).label(
                    "referenced_evidence_count"
                ),
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
        is_ai_original = (
            str(row.is_ai_original).lower() == "true" if row.is_ai_original is not None else True
        )
        ref_count = (
            row.referenced_evidence_count if row.referenced_evidence_count is not None else 0
        )
        return {
            "date": row.date or "",
            "time": row.time or "",
            "index": row.index or 1,
            "title": row.title or "",
            "description": row.description or "",
            "tags": tags,
            "is_ai_original": is_ai_original,
            "referenced_evidence_count": ref_count,
        }

    def remove_evidence_from_json(self, complaint_id: UUID, timeline_evidence_id: UUID) -> None:
        """timeline_json에서 timeline_evidence_id에 해당하는 evidence 제거. 같은 날짜/시각의 나머지 evidences는 index -1."""
        timeline = self.get_by_complaint_id(complaint_id)
        if not timeline:
            return
        items = timeline.timeline_json.get("items", [])
        ev_id_str = str(timeline_evidence_id)
        for dg in items:
            for evt in dg.get("events", []):
                evidences = evt.get("evidences", [])
                for i, ev in enumerate(evidences):
                    eid = ev.get("timeline_evidence_id") or ev.get("id")
                    if eid and str(eid) == ev_id_str:
                        removed_index = ev.get("index", 1)
                        evidences.pop(i)
                        for other in evidences:
                            if other.get("index", 1) > removed_index:
                                other["index"] = other.get("index", 1) - 1
                        if not evidences:
                            dg["events"].remove(evt)
                        if not dg.get("events"):
                            items.remove(dg)
                        timeline.timeline_json["items"] = [x for x in items if x.get("events")]
                        flag_modified(timeline, "timeline_json")
                        timeline.need_timeline_pdf_regeneration = True
                        return

    def update_referenced_evidence_count(
        self, complaint_id: UUID, timeline_evidence_id: UUID, count: int
    ) -> None:
        """timeline_json에서 해당 evidence의 referenced_evidence_count만 갱신."""
        timeline = self.get_by_complaint_id(complaint_id)
        if not timeline:
            return
        ev_id_str = str(timeline_evidence_id)
        for dg in timeline.timeline_json.get("items", []):
            for evt in dg.get("events", []):
                for ev in evt.get("evidences", []):
                    eid = ev.get("timeline_evidence_id") or ev.get("id")
                    if eid and str(eid) == ev_id_str:
                        ev["referenced_evidence_count"] = count
                        flag_modified(timeline, "timeline_json")
                        timeline.need_timeline_pdf_regeneration = True
                        return

    def update_evidence_json(
        self, complaint_id: UUID, timeline_evidence_id: UUID, updates: dict
    ) -> None:
        """timeline_json에서 timeline_evidence_id에 해당하는 객체 수정. date/time 변경 시 객체 이동, 동일 시각 있으면 index=max+1."""
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
        timeline.need_timeline_pdf_regeneration = True

    def add_manual_evidence_to_json(
        self, complaint_id: UUID, date: str, time: str, title: str, description: str, tags: list
    ) -> tuple[UUID, int]:
        """직접 추가 증거를 timeline_json에 추가. (timeline_evidence_id, index) 반환."""
        from uuid import uuid4

        timeline = self.get_by_complaint_id(complaint_id)
        if not timeline:
            raise ValueError("Timeline not found")
        timeline_evidence_id = uuid4()
        items = timeline.timeline_json.setdefault("items", [])

        # date 그룹 찾기 또는 생성
        dg = None
        for item in items:
            if item.get("date") == date:
                dg = item
                break
        if dg is None:
            items.append({"date": date, "events": []})
            dg = items[-1]
            items.sort(key=lambda x: x.get("date", ""))

        # time 이벤트 찾기 또는 생성
        events = dg.setdefault("events", [])
        evt = None
        for e in events:
            if e.get("time") == time:
                evt = e
                break
        if evt is None:
            events.append({"time": time, "evidences": []})
            evt = events[-1]
            events.sort(key=lambda x: x.get("time", ""))

        evidences = evt.setdefault("evidences", [])
        next_index = max((e.get("index", 1) for e in evidences), default=0) + 1
        evidences.append(
            {
                "timeline_evidence_id": str(timeline_evidence_id),
                "index": next_index,
                "title": title,
                "description": description,
                "tags": [t.value if hasattr(t, "value") else t for t in tags],
                "referenced_evidence_count": 0,
                "has_thumbnail": False,
                "thumbnail_url": "",
                "duration_seconds": None,
                "is_ai_original": False,
            }
        )
        timeline.timeline_json["items"] = [i for i in items if i.get("events")]
        flag_modified(timeline, "timeline_json")
        timeline.need_timeline_pdf_regeneration = True
        return timeline_evidence_id, next_index


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

    def delete_by_timeline_evidence_id(self, timeline_id: UUID, timeline_evidence_id: UUID) -> int:
        """timeline_evidence_id에 해당하는 timeline_evidences 전부 삭제. 삭제된 row 수 반환."""
        from sqlalchemy import delete as sql_delete

        result = self.db.execute(
            sql_delete(TimelineEvidence).where(
                TimelineEvidence.timeline_id == timeline_id,
                TimelineEvidence.timeline_evidence_id == timeline_evidence_id,
            )
        )
        return result.rowcount


class TimelineManualEvidenceRepository(BaseRepository):
    model_class = TimelineManualEvidence
    pk_attr = "id"

    def list_by_timeline_evidence_id(
        self, timeline_id: UUID, timeline_evidence_id: UUID
    ) -> list[TimelineManualEvidence]:
        """timeline_evidence_id에 해당하는 직접 추가 증거 목록 조회 (N+1 방지)."""
        return (
            self.db.query(TimelineManualEvidence)
            .join(
                TimelineEvidence,
                TimelineManualEvidence.id == TimelineEvidence.referenced_manual_evidence_id,
            )
            .filter(
                TimelineEvidence.timeline_id == timeline_id,
                TimelineEvidence.timeline_evidence_id == timeline_evidence_id,
                TimelineEvidence.is_original_evidence.is_(False),
            )
            .order_by(TimelineEvidence.index)
            .all()
        )
