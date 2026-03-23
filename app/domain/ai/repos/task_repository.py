from uuid import UUID

from app.base.base_repository import BaseRepository
from app.domain.ai.models import Task, TaskType


class TaskRepository(BaseRepository):
    model_class = Task
    pk_attr = "id"

    def get_latest_timeline_by_complaint_id(self, complaint_id: UUID) -> Task | None:
        """complaint_id·type=TIMELINE인 태스크 중 created_at이 가장 최근인 것 반환."""
        return (
            self.db.query(Task)
            .filter(Task.complaint_id == complaint_id, Task.type == TaskType.TIMELINE)
            .order_by(Task.created_at.desc())
            .first()
        )
