from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.base.base_error import CodeException
from app.core.auth import AuthUser
from app.core.aws import send_sqs_message
from app.domain.ai.errors.current_task_error import CurrentTaskErrorCode
from app.domain.ai.models import LLMType, Task, TaskStatus, TaskType
from app.domain.ai.repos.task_repository import TaskRepository
from app.domain.ai.schemas.responses import NeedToGenerateResponse, TaskIdResponse
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

    def get_current_task_id(
        self,
        complaint: Complaint,
        db: Session,
        *,
        expected_step: ComplaintStep,
        task_type: TaskType,
    ) -> TaskIdResponse:
        if complaint.step != expected_step:
            raise CodeException(
                code=CurrentTaskErrorCode.NOT_GENERATING,
                message="AI 생성 중이 아닐 때는 현재 태스크 ID를 조회할 수 없습니다.",
                debug_message=(
                    f"complaint.step이 {expected_step.value}(생성 중)이 아닙니다. "
                    f"현재: {complaint.step.value}"
                ),
                status_code=400,
            )
        task = TaskRepository(db).get_latest_by_complaint_id_and_type(
            complaint.complaint_id, task_type
        )
        return TaskIdResponse(task_id=task.id if task else None)

    def request_timeline_generate(
        self,
        complaint: Complaint,
        db: Session,
        llm_type: LLMType,
    ) -> TaskIdResponse:
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

        send_sqs_message(
            {
                "task_id": str(task_id),
                "type": "timeline",
                "complaint_id": str(complaint.complaint_id),
                "llm_type": llm_type.value,
            }
        )

        return TaskIdResponse(task_id=task_id)

    def request_document_generate(
        self,
        complaint: Complaint,
        db: Session,
        current_user: AuthUser,
    ) -> TaskIdResponse:
        task_id = uuid4()

        complaint.step = ComplaintStep.DOCUMENT_GENERATING

        task = Task(
            id=task_id,
            type=TaskType.DOCUMENT,
            status=TaskStatus.PENDING,
            complaint_id=complaint.complaint_id,
        )
        TaskRepository(db).create(task)
        db.commit()

        send_sqs_message(
            {
                "task_id": str(task_id),
                "type": "document",
                "complaint_id": str(complaint.complaint_id),
                "user_name": current_user.name,
                "user_birthdate": current_user.birthdate,
            }
        )

        return TaskIdResponse(task_id=task_id)


ai_service = AIService()
