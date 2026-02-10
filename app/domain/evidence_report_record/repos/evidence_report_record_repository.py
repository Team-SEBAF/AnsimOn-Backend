from uuid import UUID

from app.domain.evidence.repos.evidence_repository_base import EvidenceRepositoryBase

from ..models.evidence_report_record_model import EvidenceReportRecord


class EvidenceReportRecordRepository(EvidenceRepositoryBase):
    model_class = EvidenceReportRecord
    pk_attr = "report_record_id"

    def get(self, report_record_id: UUID) -> EvidenceReportRecord | None:
        return super().get(report_record_id)

    def delete(self, report_record: EvidenceReportRecord) -> None:
        super().delete(report_record)
