from datetime import datetime
from io import BytesIO

# from pathlib import Path
from urllib.parse import quote
from zipfile import ZIP_DEFLATED, ZipFile
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.aws import generate_presigned_get_url, head_s3_object, upload_fileobj
from app.core.settings import settings
from app.doc_generator.complaint_docx.builder import build_complaint_docx_bytes
from app.doc_generator.statement_docx.builder import build_statement_docx_bytes
from app.domain.complaint import Complaint
from app.domain.document.repos import DocumentRepository
from app.domain.document.service import document_service

# def _doc_results_dir() -> Path:
#     """프로젝트 app/doc_generator/results (로컬 미리보기)."""
#     return Path(__file__).resolve().parents[2] / "doc_generator" / "results"


# def _next_results_sequence(results_dir: Path, suffix: str) -> int:
#     """results 내 *{suffix} 파일명 선두 숫자 최댓값 + 1."""
#     max_n = 0
#     for f in results_dir.glob(f"*{suffix}"):
#         stem = f.stem
#         head = stem.split("_", 1)[0] if "_" in stem else stem
#         if head.isdigit():
#             max_n = max(max_n, int(head))
#     return max_n + 1


class DocumentDownloadService:
    # def save_complaint_docx_preview_local(
    #     self,
    #     complaint: Complaint,
    #     db: Session,
    # ) -> Path:
    #     """
    #     complaint_form_data를 조회해 고소장 docx를 생성·doc_generator/results/에 저장 (S3 없음).
    #     파일명: {n}_complaint.docx
    #     """
    #     complaint_form_data = document_service.get_complaint_form_data(
    #         complaint.complaint_id,
    #         db,
    #     )

    #     results_dir = _doc_results_dir()
    #     results_dir.mkdir(parents=True, exist_ok=True)
    #     next_n = _next_results_sequence(results_dir, "_complaint.docx")

    #     out_path = results_dir / f"{next_n}_complaint.docx"
    #     out_path.write_bytes(build_complaint_docx_bytes(complaint_form_data))
    #     return out_path

    # def save_statement_docx_preview_local(
    #     self,
    #     complaint: Complaint,
    #     db: Session,
    # ) -> Path:
    #     """
    #     statement_form_data를 조회해 진술서 docx를 생성·doc_generator/results/에 저장 (S3 없음).
    #     파일명: {n}_statement.docx
    #     """
    #     statement_form_data = document_service.get_statement_form_data(
    #         complaint.complaint_id,
    #         db,
    #     )

    #     results_dir = _doc_results_dir()
    #     results_dir.mkdir(parents=True, exist_ok=True)
    #     next_n = _next_results_sequence(results_dir, "_statement.docx")

    #     out_path = results_dir / f"{next_n}_statement.docx"
    #     out_path.write_bytes(build_statement_docx_bytes(statement_form_data))
    #     return out_path

    def create_download_zip(
        self,
        complaint: Complaint,
        db: Session,
    ) -> tuple[bytes, str]:
        """
        고소장·진술서 docx를 담은 ZIP 생성 후 S3 업로드.
        - need_complaint_pdf_regeneration · need_statement_pdf_regeneration 둘 다 False이고 동일 S3 키에 객체가 있으면 생성 생략(빈 bytes 반환).
        - 하나라도 True이면 두 docx 모두 새로 만들고 ZIP 전체를 덮어쓴 뒤 플래그를 둘 다 False로 맞춤.
        """
        zip_upload_s3_key = (
            f"{complaint.user_sub}/complaints/{complaint.complaint_id}/"
            "document-download/download.zip"
        )
        doc_row = DocumentRepository(db).get_by_complaint_id(complaint.complaint_id)
        assert doc_row is not None

        zip_exists = head_s3_object(settings.S3_BUCKET_NAME, zip_upload_s3_key) is not None
        if (
            not doc_row.need_complaint_pdf_regeneration
            and not doc_row.need_statement_pdf_regeneration
            and zip_exists
        ):
            return b"", zip_upload_s3_key

        complaint_form_data = document_service.get_complaint_form_data(
            complaint.complaint_id,
            db,
        )
        statement_form_data = document_service.get_statement_form_data(
            complaint.complaint_id,
            db,
        )
        complaint_bytes = build_complaint_docx_bytes(complaint_form_data)
        statement_bytes = build_statement_docx_bytes(statement_form_data)

        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
            zf.writestr("고소장.docx", complaint_bytes)
            zf.writestr("진술서.docx", statement_bytes)
        buffer.seek(0)
        zip_bytes = buffer.getvalue()

        upload_fileobj(
            fileobj=BytesIO(zip_bytes),
            bucket=settings.S3_BUCKET_NAME,
            key=zip_upload_s3_key,
            content_type="application/zip",
        )
        doc_row.need_complaint_pdf_regeneration = False
        doc_row.need_statement_pdf_regeneration = False
        db.commit()
        return zip_bytes, zip_upload_s3_key

    def get_download_zip_presigned_url(
        self,
        complaint: Complaint,
        db: Session,
        expires_in: int = 3600,
    ) -> str:
        """ZIP이 없거나 재생성이 필요하면 생성·업로드 후 presigned GET URL 반환."""
        _, s3_key = self.create_download_zip(complaint=complaint, db=db)
        date_str = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%y%m%d")
        filename = f"안심온_고소장진술서_{date_str}.zip"
        ascii_fallback = f"AnsimOn_complaint_statement_{date_str}.zip"
        encoded = quote(filename, safe="")
        content_disp = f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded}"
        return generate_presigned_get_url(
            bucket=settings.S3_BUCKET_NAME,
            key=s3_key,
            expires_in=expires_in,
            response_content_disposition=content_disp,
        )


document_download_service = DocumentDownloadService()
