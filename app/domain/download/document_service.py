from pathlib import Path

from sqlalchemy.orm import Session

from app.doc_generator.complaint_docx.builder import build_complaint_docx_bytes
from app.doc_generator.statement_docx.builder import build_statement_docx_bytes
from app.domain.complaint import Complaint
from app.domain.document.service import document_service


def _doc_results_dir() -> Path:
    """프로젝트 app/doc_generator/results (로컬 미리보기)."""
    return Path(__file__).resolve().parents[2] / "doc_generator" / "results"


def _next_results_sequence(results_dir: Path, suffix: str) -> int:
    """results 내 *{suffix} 파일명 선두 숫자 최댓값 + 1."""
    max_n = 0
    for f in results_dir.glob(f"*{suffix}"):
        stem = f.stem
        head = stem.split("_", 1)[0] if "_" in stem else stem
        if head.isdigit():
            max_n = max(max_n, int(head))
    return max_n + 1


class DocumentDownloadService:
    def save_complaint_docx_preview_local(
        self,
        complaint: Complaint,
        db: Session,
    ) -> Path:
        """
        complaint_form_data를 조회해 고소장 docx를 생성·doc_generator/results/에 저장 (S3 없음).
        파일명: {n}_complaint.docx
        """
        complaint_form_data = document_service.get_complaint_form_data(
            complaint.complaint_id,
            db,
        )

        results_dir = _doc_results_dir()
        results_dir.mkdir(parents=True, exist_ok=True)
        next_n = _next_results_sequence(results_dir, "_complaint.docx")

        out_path = results_dir / f"{next_n}_complaint.docx"
        out_path.write_bytes(build_complaint_docx_bytes(complaint_form_data))
        return out_path

    def save_statement_docx_preview_local(
        self,
        complaint: Complaint,
        db: Session,
    ) -> Path:
        """
        statement_form_data를 조회해 진술서 docx를 생성·doc_generator/results/에 저장 (S3 없음).
        파일명: {n}_statement.docx
        """
        statement_form_data = document_service.get_statement_form_data(
            complaint.complaint_id,
            db,
        )

        results_dir = _doc_results_dir()
        results_dir.mkdir(parents=True, exist_ok=True)
        next_n = _next_results_sequence(results_dir, "_statement.docx")

        out_path = results_dir / f"{next_n}_statement.docx"
        out_path.write_bytes(build_statement_docx_bytes(statement_form_data))
        return out_path


document_download_service = DocumentDownloadService()
