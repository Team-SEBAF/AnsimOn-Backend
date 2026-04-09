from __future__ import annotations

from datetime import datetime
from io import BytesIO
from urllib.parse import quote
from zipfile import ZIP_DEFLATED, ZipFile
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.auth import AuthUser
from app.core.aws import (
    download_s3_object,
    generate_presigned_get_url,
    head_s3_object,
    upload_fileobj,
)
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.document.repos import DocumentRepository
from app.domain.download.document_service import document_download_service
from app.domain.download.timeline_service import timeline_download_service
from app.domain.timeline.repos import TimelineRepository


def _timeline_zip_inner_root(namelist: list[str]) -> str:
    for name in namelist:
        if "/" in name:
            return name.split("/")[0]
    return ""


def _merge_timeline_zip_flat_root(
    timeline_zip_bytes: bytes,
    document_zip_bytes: bytes,
) -> bytes:
    """
    타임라인 ZIP 최상위 폴더(예: 안심온_증거분석타임라인)를 제거하고
    대조 증거 모음·타임라인.pdf를 루트에 둔 뒤 고소장·진술서 docx를 합친다.
    """
    out = BytesIO()
    with ZipFile(BytesIO(timeline_zip_bytes), "r") as tz:
        root = _timeline_zip_inner_root(tz.namelist())
        with ZipFile(out, "w", ZIP_DEFLATED) as oz:
            for info in tz.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                if root and name.startswith(root + "/"):
                    inner = name[len(root) + 1 :]
                elif root and name == root:
                    continue
                else:
                    inner = name
                if not inner:
                    continue
                oz.writestr(inner, tz.read(name))

            with ZipFile(BytesIO(document_zip_bytes), "r") as dz:
                for info in dz.infolist():
                    if info.is_dir():
                        continue
                    oz.writestr(info.filename, dz.read(info.filename))

    out.seek(0)
    return out.read()


class AllDownloadService:
    def create_all_download_zip(
        self,
        complaint: Complaint,
        current_user: AuthUser,
        db: Session,
    ) -> tuple[bytes, str]:
        """
        통합 ZIP(all-download/download.zip) 생성·S3 업로드.
        타임라인·문서 각각 create_download_zip으로 최신화한 뒤, 두 ZIP을 풀어 계층을 맞춰 재패킹한다.
        네 가지 need_* 가 모두 False이고 통합 ZIP이 이미 있으면 스킵(빈 bytes).
        """
        zip_upload_s3_key = (
            f"{complaint.user_sub}/complaints/{complaint.complaint_id}/all-download/download.zip"
        )
        timeline_repo = TimelineRepository(db)
        timeline = timeline_repo.get_by_complaint_id(complaint.complaint_id)
        doc_row = DocumentRepository(db).get_by_complaint_id(complaint.complaint_id)
        assert doc_row is not None

        timeline_fresh = (
            timeline
            and not timeline.need_evidence_collection_regeneration
            and not timeline.need_timeline_pdf_regeneration
        )
        doc_fresh = (
            not doc_row.need_complaint_pdf_regeneration
            and not doc_row.need_statement_pdf_regeneration
        )
        all_exists = head_s3_object(settings.S3_BUCKET_NAME, zip_upload_s3_key) is not None

        if timeline_fresh and doc_fresh and all_exists:
            return b"", zip_upload_s3_key

        timeline_bytes, timeline_key = timeline_download_service.create_download_zip(
            complaint=complaint,
            current_user=current_user,
            db=db,
        )
        if not timeline_bytes:
            timeline_bytes = download_s3_object(settings.S3_BUCKET_NAME, timeline_key)

        document_bytes, document_key = document_download_service.create_download_zip(
            complaint=complaint,
            db=db,
        )
        if not document_bytes:
            document_bytes = download_s3_object(settings.S3_BUCKET_NAME, document_key)

        merged = _merge_timeline_zip_flat_root(timeline_bytes, document_bytes)
        upload_fileobj(
            fileobj=BytesIO(merged),
            bucket=settings.S3_BUCKET_NAME,
            key=zip_upload_s3_key,
            content_type="application/zip",
        )
        return merged, zip_upload_s3_key

    def get_all_download_zip_presigned_url(
        self,
        complaint: Complaint,
        current_user: AuthUser,
        db: Session,
        expires_in: int = 3600,
    ) -> str:
        _, s3_key = self.create_all_download_zip(
            complaint=complaint,
            current_user=current_user,
            db=db,
        )
        date_str = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%y%m%d")
        filename = f"안심온_타임라인_고소장진술서_{date_str}.zip"
        ascii_fallback = f"AnsimOn_timeline_complaint_statement_{date_str}.zip"
        encoded = quote(filename, safe="")
        content_disp = f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded}"
        return generate_presigned_get_url(
            bucket=settings.S3_BUCKET_NAME,
            key=s3_key,
            expires_in=expires_in,
            response_content_disposition=content_disp,
        )


all_download_service = AllDownloadService()
