from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.aws import send_sqs_message
from app.domain.ai.errors.current_task_error import CurrentTaskErrorCode
from app.domain.ai.models import LLMType, Task, TaskStatus, TaskType
from app.domain.ai.repos.task_repository import TaskRepository
from app.domain.ai.schemas.responses import (
    NeedToGenerateResponse,
    TaskRequestResponse,
    TimelineTaskIdResponse,
)
from app.domain.complaint import Complaint
from app.domain.complaint.models.complaint_model import ComplaintStep
from app.domain.document.repos.document_repository import DocumentRepository
from app.domain.timeline.errors.get_timeline_error import GetTimelineErrorCode
from app.domain.timeline.repos.timeline_repository import TimelineRepository


class AIService:
    def get_need_to_generate(self, complaint_id, db: Session):
        timeline_repo = TimelineRepository(db)
        timeline = timeline_repo.get_by_complaint_id(complaint_id)
        need = timeline.need_timeline_regeneration if timeline else True
        return NeedToGenerateResponse(need_to_generate=need)

    def get_current_timeline_task_id(self, complaint: Complaint, db: Session):
        if complaint.step != ComplaintStep.TIMELINE_GENERATING:
            raise CodeException(
                code=CurrentTaskErrorCode.NOT_TIMELINE_GENERATING,
                message="타임라인 생성 중이 아닐 때는 현재 태스크 ID를 조회할 수 없습니다.",
                status_code=400,
            )
        task = TaskRepository(db).get_latest_timeline_by_complaint_id(complaint.complaint_id)
        return TimelineTaskIdResponse(task_id=task.id if task else None)

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
        TaskRepository(db).create(task)
        db.commit()

        message = {
            "task_id": str(task_id),
            "type": "timeline",
            "complaint_id": str(complaint.complaint_id),
            "llm_type": llm_type.value,
        }

        send_sqs_message(message)

        return TaskRequestResponse(task_id=task_id)

    def get_document_need_to_generate(
        self, complaint_id: UUID, db: Session
    ) -> NeedToGenerateResponse:
        timeline_repo = TimelineRepository(db)
        timeline = timeline_repo.get_by_complaint_id(complaint_id)
        if timeline is None:
            raise CodeException(
                code=GetTimelineErrorCode.TIMELINE_NOT_FOUND,
                message="타임라인을 찾을 수 없습니다.",
                debug_message=f"complaint_id: {complaint_id}에 해당하는 타임라인이 없습니다.",
                status_code=404,
            )
        document = DocumentRepository(db).get_by_complaint_id(complaint_id)
        need_to_generate = document is None or timeline.need_timeline_pdf_regeneration
        return NeedToGenerateResponse(need_to_generate=need_to_generate)


ai_service = AIService()
