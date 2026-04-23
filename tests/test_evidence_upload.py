import logging
from pathlib import Path
from typing import Any

from tests.evidence_test_common import BaseEvidenceRunner, EvidenceApiSpec

DATASET_ROOT_DIR = Path(__file__).resolve().parent / "integration_test_set" / "evidence_upload_test"
logger = logging.getLogger(__name__)


class EvidenceUploadTestRunner(BaseEvidenceRunner):
    def run(self, spec: EvidenceApiSpec) -> None:
        logger.info("=== [%s] 업로드 테스트 시작 ===", spec.evidence_type)
        files = self.dataset_files(spec, label="테스트")
        presigned_items = self.build_presigned_items(files, include_duration=False)
        presigned_result = self.request_presigned_url(spec, presigned_items)
        register_items, _ = self.upload_and_build_register_items(spec, files, presigned_result)

        response = self.request_register(spec, register_items)
        assert response.status_code == 200, (
            f"[{spec.evidence_type}] register 실패: "
            f"status={response.status_code}, body={response.text}"
        )
        logger.info("=== [%s] 업로드 테스트 완료 ===", spec.evidence_type)


def _runner(integration_context: dict[str, str], client: Any) -> EvidenceUploadTestRunner:
    return EvidenceUploadTestRunner(
        client=client,
        complaint_id=integration_context["complaint_id"],
        access_token=integration_context["access_token"],
        dataset_root=DATASET_ROOT_DIR,
    )


def test_evidence_upload_message_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceApiSpec(
            evidence_type="MESSAGE",
            dataset_dir_name="MESSAGE",
            register_path_suffix="evidences/messages/register",
            register_id_field="messageId",
        )
    )


def test_evidence_upload_voice_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceApiSpec(
            evidence_type="VOICE",
            dataset_dir_name="VOICE",
            register_path_suffix="evidences/voices/register",
            register_id_field="voiceId",
        )
    )


def test_evidence_upload_victim_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceApiSpec(
            evidence_type="VICTIM",
            dataset_dir_name="VICTIM",
            register_path_suffix="evidences/victims/register",
            register_id_field="victimId",
        )
    )


def test_evidence_upload_report_record_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceApiSpec(
            evidence_type="REPORT_RECORD",
            dataset_dir_name="REPORT_RECORD",
            register_path_suffix="evidences/report-records/register",
            register_id_field="reportRecordId",
        )
    )


def test_evidence_upload_incident_log_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceApiSpec(
            evidence_type="INCIDENT_LOG",
            dataset_dir_name="INCIDENT_LOG",
            register_path_suffix="evidences/incident-logs/file/register",
            register_id_field="incidentLogId",
        )
    )
