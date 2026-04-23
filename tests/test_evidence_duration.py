import logging
from pathlib import Path
from typing import Any

from tests.evidence_test_common import BaseEvidenceRunner, EvidenceApiSpec

DATASET_ROOT_DIR = (
    Path(__file__).resolve().parent / "integration_test_set" / "evidence_duration_test"
)
logger = logging.getLogger(__name__)


class EvidenceDurationTestRunner(BaseEvidenceRunner):
    def run(self, spec: EvidenceApiSpec) -> None:
        logger.info("=== [%s] duration 검증 테스트 시작 ===", spec.evidence_type)
        files = self.dataset_files(spec, label="duration 테스트")
        presigned_items = self.build_presigned_items(files, include_duration=True)
        presigned_result = self.request_presigned_url(spec, presigned_items)
        register_items, requested_evidence_ids = self.upload_and_build_register_items(
            spec, files, presigned_result
        )
        self.assert_register_duration_validation_failed(
            spec, register_items, requested_evidence_ids
        )
        logger.info("[%s] duration 검증 실패 응답 확인 완료", spec.evidence_type)
        logger.info("=== [%s] duration 검증 테스트 완료 ===", spec.evidence_type)

    def assert_register_duration_validation_failed(
        self,
        spec: EvidenceApiSpec,
        register_items: list[dict[str, Any]],
        requested_evidence_ids: list[str],
    ) -> None:
        response = self.request_register(spec, register_items)
        assert response.status_code == 400, (
            f"[{spec.evidence_type}] register 예상 400 실패: "
            f"status={response.status_code}, body={response.text}"
        )

        body = response.json()
        assert body["code"] == "EVIDENCE_REGISTER_VALIDATION_FAILED"

        duration_failed_ids = body.get("duration_seconds_failed_evidence_ids", [])
        for evidence_id in requested_evidence_ids:
            assert evidence_id in duration_failed_ids, (
                f"[{spec.evidence_type}] duration 실패 목록 누락: evidence_id={evidence_id}, "
                f"duration_failed_ids={duration_failed_ids}"
            )


def _runner(integration_context: dict[str, str], client: Any) -> EvidenceDurationTestRunner:
    return EvidenceDurationTestRunner(
        client=client,
        complaint_id=integration_context["complaint_id"],
        access_token=integration_context["access_token"],
        dataset_root=DATASET_ROOT_DIR,
    )


def test_evidence_duration_voice_validation_failed(
    integration_context: dict[str, str], client: Any
):
    _runner(integration_context, client).run(
        EvidenceApiSpec(
            evidence_type="VOICE",
            dataset_dir_name="VOICE",
            register_path_suffix="evidences/voices/register",
            register_id_field="voiceId",
        )
    )


def test_evidence_duration_victim_validation_failed(
    integration_context: dict[str, str], client: Any
):
    _runner(integration_context, client).run(
        EvidenceApiSpec(
            evidence_type="VICTIM",
            dataset_dir_name="VICTIM",
            register_path_suffix="evidences/victims/register",
            register_id_field="victimId",
        )
    )
