from uuid import UUID

from app.base.base_repository import BaseRepository
from app.domain.ai.models import Task, TaskType


class TaskRepository(BaseRepository):
    model_class = Task
    pk_attr = "id"

    def get_latest_by_complaint_id_and_type(
        self, complaint_id: UUID, task_type: TaskType
    ) -> Task | None:
        """complaint_id·해당 type 태스크 중 created_at이 가장 최근인 것 반환."""
        return (
            self.db.query(Task)
            .filter(Task.complaint_id == complaint_id, Task.type == task_type)
            .order_by(Task.created_at.desc())
            .first()
        )
