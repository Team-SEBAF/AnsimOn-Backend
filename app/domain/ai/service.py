from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.aws import send_sqs_message
from app.domain.ai.models import Task, TaskStatus, TaskType
from app.domain.ai.schemas.responses import TaskRequestResponse
from app.domain.complaint import Complaint


class AIService:
    def request_generate_timeline(self, complaint: Complaint, db: Session) -> TaskRequestResponse:
        task_id = uuid4()

        task = Task(
            id=task_id,
            type=TaskType.TIMELINE,
            status=TaskStatus.PENDING,
            complaint_id=complaint.complaint_id,
        )
        db.add(task)
        db.commit()

        message = {
            "task_id": str(task_id),
            "type": "timeline",
            "complaint_id": str(complaint.complaint_id),
        }

        send_sqs_message(message)

        return TaskRequestResponse(task_id=task_id)


ai_service = AIService()
