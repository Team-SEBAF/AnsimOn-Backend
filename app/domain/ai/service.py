from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.aws import send_sqs_message
from app.domain.ai.models import LLMType, Task, TaskStatus, TaskType
from app.domain.ai.schemas.responses import TaskRequestResponse, TimelineNeedToGenerateResponse
from app.domain.complaint import Complaint
from app.domain.complaint.models.complaint_model import ComplaintStep
from app.domain.timeline.repos.timeline_repository import TimelineRepository


class AIService:
    def get_need_to_generate(self, complaint_id, db: Session):
        timeline_repo = TimelineRepository(db)
        timeline = timeline_repo.get_by_complaint_id(complaint_id)
        need = timeline.need_timeline_regeneration if timeline else True
        return TimelineNeedToGenerateResponse(need_to_generate=need)

    def request_generate_timeline(
        self, complaint: Complaint, db: Session, llm_type: LLMType
    ) -> TaskRequestResponse:
        task_id = uuid4()

        complaint.step = ComplaintStep.TIMELINE_GENERATING

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
            "llm_type": llm_type.value,
        }

        send_sqs_message(message)

        return TaskRequestResponse(task_id=task_id)


ai_service = AIService()
