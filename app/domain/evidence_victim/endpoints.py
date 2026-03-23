from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import app.domain.evidence.errors as evidence_errors
from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.evidence.constant import EVIDENCE_VICTIM_RESTRICT
from app.domain.evidence_victim import schemas
from app.domain.evidence_victim.service import evidence_victim_service

router = APIRouter(prefix="/api/v1", tags=["Evidence Victim"])


@router.post(
    "/{complaint_id}/evidences/victims/register",
    summary=f"VICTIM 타입 증거 Presigned URL로 S3 업로드 완료 후, 메타데이터 DB 저장 + 썸네일/상세 이미지 생성 (복수 업로드 지원, 최대 {EVIDENCE_VICTIM_RESTRICT.max_count}개)",
    description="Presigned URL로 S3 업로드 완료 후 호출하세요. 썸네일/상세 이미지는 백엔드에서 생성합니다.",
    response_model=schemas.EvidenceVictimRegisterListResponse,
    responses=evidence_errors.REGISTER_EVIDENCE_ERRORS_RESPONSES,
)
def register_victim(
    complaint: Complaint = Depends(get_owned_complaint),
    request: schemas.EvidenceVictimRegisterRequest = ...,
    db: Session = Depends(get_db),
):
    return evidence_victim_service.register_victim(
        complaint=complaint,
        request=request,
        db=db,
    )


# @router.get(
#     "/{complaint_id}/evidences/victims/previews",
#     summary="VICTIM 타입 증거 프리뷰 리스트 조회 (썸네일 이미지 1시간 유효) [미사용]",
#     description="VICTIM 타입 증거 프리뷰 리스트를 조회합니다.",
#     response_model=schemas.EvidenceVictimPreviewListResponse,
# )
# def get_evidence_victim_previews(
#     complaint: Complaint = Depends(get_owned_complaint),
#     limit: int = Query(5, ge=1, le=20),
#     db: Session = Depends(get_db),
# ):
#     return evidence_victim_service.get_preview_victims(
#         complaint=complaint,
#         limit=limit,
#         db=db,
#     )


@router.get(
    "/{complaint_id}/evidences/victims/details",
    summary="VICTIM 타입 증거 상세 리스트 조회 (썸네일 이미지 30분 유효)",
    description="VICTIM 타입 증거 상세 리스트를 조회합니다.",
    response_model=schemas.EvidenceVictimDetailListResponse,
)
def get_evidence_victim_details(
    complaint: Complaint = Depends(get_owned_complaint),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return evidence_victim_service.get_detail_victims(
        complaint=complaint,
        limit=limit,
        db=db,
    )


# @router.get(
#     "/evidence/victim/{victim_id}/original",
#     summary="VICTIM 타입 증거 영상 원본 조회 (원본 영상 10분 유효) [미사용]",
#     description="VICTIM 타입 증거 영상 원본을 조회합니다.",
#     response_model=schemas.EvidenceVictimOriginalResponse,
#     responses=evidence_errors.GET_EVIDENCE_ERRORS_RESPONSES,
# )
# def get_evidence_victim_original(
#     victim_id: UUID,
#     current_user: AuthUser = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     return evidence_victim_service.get_original_victim(
#         victim_id=victim_id,
#         current_user=current_user,
#         db=db,
#     )
