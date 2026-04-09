"""ZIP/PDF 다운로드용 임시 엔드포인트."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import AuthUser, get_current_user
from app.core.database import get_db
from app.domain.complaint import Complaint, get_owned_complaint
from app.domain.download.document_service import document_download_service
from app.domain.download.schemas.responses import TimelineDownloadZipResponse
from app.domain.download.timeline_service import timeline_download_service

router = APIRouter(prefix="/api/v1", tags=["Download"])


# @router.get(
#     "/{complaint_id}/timeline/download/preview",
#     summary="[임시] 다운로드용 타임라인 JSON 미리보기",
#     description="ZIP/PDF 생성에 사용할 전처리된 타임라인 JSON. evidences_numstring_s3_key_list 포함.",
# )
# def get_timeline_for_download_preview(
#     complaint: Complaint = Depends(get_owned_complaint),
#     db: Session = Depends(get_db),
# ):
#     return timeline_download_service._get_timeline_for_download(
#         complaint=complaint,
#         db=db,
#     )


# @router.get(
#     "/{complaint_id}/timeline/download/pdf",
#     summary="[임시] 타임라인 PDF 생성",
#     description="개발용 타임라인 PDF 생성. 로컬일 때 pdf_generator/results/에 저장 후 성공 메시지 반환.",
# )
# def get_timeline_pdf_preview(
#     complaint: Complaint = Depends(get_owned_complaint),
#     current_user: AuthUser = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     author = current_user.name or current_user.email or "-"
#     timeline_download_service.get_timeline_pdf_preview(
#         complaint=complaint,
#         author=author,
#         db=db,
#     )
#     return {"message": "저장되었습니다"}


@router.post(
    "/{complaint_id}/timeline/download/zip",
    summary="ZIP 다운로드용 presigned URL 발급",
    description="다운로드 ZIP(대조 증거 모음 + 타임라인 PDF) 생성 후 S3 업로드, presigned URL 반환.",
)
def create_download_zip(
    complaint: Complaint = Depends(get_owned_complaint),
    current_user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TimelineDownloadZipResponse:
    url = timeline_download_service.get_download_zip_presigned_url(
        complaint=complaint,
        current_user=current_user,
        db=db,
    )
    return TimelineDownloadZipResponse(download_url=url)


@router.post(
    "/{complaint_id}/document/download/complaint-docx-preview",
    summary="[임시] 고소장 DOCX 생성 (로컬 저장)",
    description="개발용. docxtpl 템플릿으로 고소장 docx를 doc_generator/results/에 {n}_complaint.docx 로 저장합니다. S3 미사용.",
)
def post_complaint_docx_preview(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    path = document_download_service.save_complaint_docx_preview_local(
        complaint=complaint,
        db=db,
    )
    return {
        "message": "저장되었습니다",
        "path": str(path),
    }


@router.post(
    "/{complaint_id}/document/download/statement-docx-preview",
    summary="[임시] 진술서 DOCX 생성 (로컬 저장)",
    description="개발용. docxtpl 템플릿으로 진술서 docx를 doc_generator/results/에 {n}_statement.docx 로 저장합니다. S3 미사용.",
)
def post_statement_docx_preview(
    complaint: Complaint = Depends(get_owned_complaint),
    db: Session = Depends(get_db),
):
    path = document_download_service.save_statement_docx_preview_local(
        complaint=complaint,
        db=db,
    )
    return {
        "message": "저장되었습니다",
        "path": str(path),
    }
