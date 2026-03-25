import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.base.base_error import register_exception_handlers
from app.core.settings import settings
from app.domain.ai.endpoints import router as ai_router
from app.domain.complaint.endpoints import router as complaint_router
from app.domain.evidence.endpoints import router as evidence_router
from app.domain.evidence_incident_log.endpoints import router as evidence_incident_log_router
from app.domain.evidence_message.endpoints import router as evidence_message_router
from app.domain.evidence_report_record.endpoints import router as evidence_report_record_router
from app.domain.evidence_victim.endpoints import router as evidence_victim_router
from app.domain.evidence_voice.endpoints import router as evidence_voice_router
from app.domain.timeline.endpoints import router as timeline_router
from app.domain.timeline_download.endpoints import router as timeline_download_router
from app.domain.user.endpoints import router as user_router
from app.sse.endpoints import router as sse_router

if settings.AWS_PROFILE:
    boto3.setup_default_session(profile_name=settings.AWS_PROFILE)

root_path = f"/{settings.env}"

app = FastAPI(title="AnsimOn Backend", root_path=root_path)

# 우선 로컬 개발용만 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 예외 핸들러 등록
register_exception_handlers(app)

if settings.env == "prod":
    from app._server_cost.prod_endpoints import router as server_cost_router

    app.include_router(server_cost_router)
elif settings.env == "dev":
    from app._server_cost.dev_endpoints import router as server_cost_router

    app.include_router(server_cost_router)

app.include_router(user_router)
app.include_router(complaint_router)
app.include_router(evidence_router)
app.include_router(evidence_message_router)
app.include_router(evidence_voice_router)
app.include_router(evidence_victim_router)
app.include_router(evidence_report_record_router)
app.include_router(evidence_incident_log_router)
app.include_router(timeline_router)
app.include_router(timeline_download_router)
app.include_router(ai_router)
app.include_router(sse_router)


handler = Mangum(app)
