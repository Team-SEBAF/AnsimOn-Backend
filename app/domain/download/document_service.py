from pathlib import Path

from sqlalchemy.orm import Session

from app.domain.complaint import Complaint
from app.domain.document.service import document_service
from app.pdf_generator.complaint_pdf.builder import build_complaint_pdf_bytes


def _pdf_results_dir() -> Path:
    """프로젝트 app/pdf_generator/results (타임라인 PDF 미리보기와 동일)."""
    return Path(__file__).resolve().parents[2] / "pdf_generator" / "results"


def _next_results_sequence(results_dir: Path) -> int:
    """results 내 *.pdf 파일명 선두 숫자(1, 2 또는 3_complaint 등) 최댓값 + 1."""
    max_n = 0
    for f in results_dir.glob("*.pdf"):
        stem = f.stem
        head = stem.split("_", 1)[0] if "_" in stem else stem
        if head.isdigit():
            max_n = max(max_n, int(head))
    return max_n + 1


class DocumentDownloadService:
    def save_complaint_pdf_preview_local(
        self,
        complaint: Complaint,
        db: Session,
    ) -> Path:
        """
        complaint_form_data를 조회해 고소장 PDF를 생성·pdf_generator/results/에 저장 (S3 없음).
        파일명: {n}_complaint.pdf
        """
        complaint_form_data = document_service.get_complaint_form_data(
            complaint.complaint_id,
            db,
        )

        results_dir = _pdf_results_dir()
        results_dir.mkdir(parents=True, exist_ok=True)
        next_n = _next_results_sequence(results_dir)

        out_path = results_dir / f"{next_n}_complaint.pdf"
        out_path.write_bytes(build_complaint_pdf_bytes(complaint_form_data))
        return out_path


document_download_service = DocumentDownloadService()
