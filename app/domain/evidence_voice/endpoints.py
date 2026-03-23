from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_VOICE_RESTRICT
from app.domain.evidence_voice import schemas
from app.domain.evidence_voice.service import evidence_voice_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Voice"])


@router.post(
    "/{complaint_id}/evidences/voices/register",
    summary=f"VOICE 타입 증거 Presigned URL로 S3 업로드 완료 후, 메타데이터 DB 저장 (복수 업로드 지원, 최대 {EVIDENCE_VOICE_RESTRICT.max_count}개)",
    description="Presigned URL로 S3 업로드 완료 후 호출하세요.",
    response_model=schemas.EvidenceVoiceRegisterListResponse,
    responses=evidence_errors.REGISTER_EVIDENCE_ERRORS_RESPONSES,
)
def register_voice(
    complaint: Complaint = Depends(get_owned_complaint),
    request: schemas.EvidenceVoiceRegisterRequest = ...,
    db: Session = Depends(get_db),
):
    return evidence_voice_service.register_voice(
        complaint=complaint,
        request=request,
        db=db,
    )


# @router.get(
#     "/{complaint_id}/evidences/voices/previews",
#     summary="VOICE 타입 증거 프리뷰 리스트 조회 [미사용]",
#     description="VOICE 타입 증거 프리뷰 리스트를 조회합니다.",
#     response_model=schemas.EvidenceVoicePreviewListResponse,
# )
# def get_evidence_voice_previews(
#     complaint: Complaint = Depends(get_owned_complaint),
#     limit: int = Query(5, ge=1, le=20),
#     db: Session = Depends(get_db),
# ):
#     return evidence_voice_service.get_preview_voices(
#         complaint=complaint,
#         limit=limit,
#         db=db,
#     )


@router.get(
    "/{complaint_id}/evidences/voices/details",
    summary="VOICE 타입 증거 상세 리스트 조회",
    description="VOICE 타입 증거 상세 리스트를 조회합니다.",
    response_model=schemas.EvidenceVoiceDetailListResponse,
)
def get_evidence_voice_details(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return evidence_voice_service.get_detail_voices(
        complaint=complaint,
        limit=limit,
        db=db,
    )


# @router.get(
#     "/evidence/voice/{voice_id}/original",
#     summary="VOICE 타입 증거 음성 원본 조회 (원본 음성 10분 유효) [미사용]",
#     description="VOICE 타입 증거 음성 원본을 조회합니다.",
#     response_model=schemas.EvidenceVoiceOriginalResponse,
#     responses=evidence_errors.GET_EVIDENCE_ERRORS_RESPONSES,
# )
# def get_evidence_voice_original(
#     voice_id: UUID,
#     current_user: AuthUser = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     return evidence_voice_service.get_original_voice(
#         voice_id=voice_id,
#         current_user=current_user,
#         db=db,
#     )
