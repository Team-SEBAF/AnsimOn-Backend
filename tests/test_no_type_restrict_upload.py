import logging
from pathlib import Path
from typing import Any

import httpx

from tests.evidence_test_common import BaseEvidenceRunner, EvidenceApiSpec

DATASET_ROOT_DIR = Path(__file__).resolve().parent / "integration_test_set"
DATASET_DIR_NAME = "no_type_restrict_file_test"
logger = logging.getLogger(__name__)


class BaseNoTypeRestrictUploadRunner(BaseEvidenceRunner):
    def dataset_files_for_no_type_restrict(self) -> list[Path]:
        return self.dataset_files(
            EvidenceApiSpec(
                evidence_type="NO_TYPE_RESTRICT",
                dataset_dir_name=DATASET_DIR_NAME,
                register_path_suffix="",
                register_id_field="",
            ),
            label="무-제한 타입 테스트",
        )

    def upload_and_build_register_items(
        self,
        files: list[Path],
        presigned_items: list[dict[str, Any]],
        register_id_field: str,
    ) -> list[dict[str, Any]]:
        items_by_index = {item["index"]: item for item in presigned_items}
        register_items: list[dict[str, Any]] = []

        logger.info("[공통] presigned-url로 파일 업로드 시작")
        for index, file_path in enumerate(files):
            presigned_item = items_by_index[index]
            logger.info("[공통] 파일 업로드 중 index=%s name=%s", index, file_path.name)
            upload_response = httpx.put(
                presigned_item["url"],
                content=file_path.read_bytes(),
                headers={"Content-Type": self.content_type(file_path)},
                timeout=60.0,
            )
            assert upload_response.status_code == 200, (
                "[공통] 파일 업로드 실패: "
                f"file={file_path.name}, status={upload_response.status_code}, "
                f"body={upload_response.text}"
            )
            logger.info("[공통] 파일 업로드 성공 index=%s name=%s", index, file_path.name)
            register_items.append(
                {
                    register_id_field: presigned_item[register_id_field],
                    "filename": file_path.name,
                }
            )
        return register_items


class IncidentLogAttachmentUploadTestRunner(BaseNoTypeRestrictUploadRunner):
    def run(self) -> None:
        logger.info("=== [INCIDENT_LOG_FORM_DATA_ATTACHMENT] 업로드 테스트 시작 ===")
        files = self.dataset_files_for_no_type_restrict()
        incident_log_id = self.create_incident_log_form_data()
        presigned_items = self.build_presigned_items(files)
        presigned_result = self.request_incident_log_attachment_presigned_url(
            incident_log_id=incident_log_id,
            items=presigned_items,
        )
        register_items = self.upload_and_build_register_items(
            files=files,
            presigned_items=presigned_result,
            register_id_field="attachment_id",
        )
        register_response = self.request_incident_log_attachment_register(
            incident_log_id=incident_log_id,
            register_items=register_items,
        )
        assert register_response.status_code == 200, (
            "[INCIDENT_LOG_FORM_DATA_ATTACHMENT] register 실패: "
            f"status={register_response.status_code}, body={register_response.text}"
        )
        assert len(register_response.json()["items"]) == len(files)
        logger.info("=== [INCIDENT_LOG_FORM_DATA_ATTACHMENT] 업로드 테스트 완료 ===")

    def create_incident_log_form_data(self) -> str:
        logger.info("[INCIDENT_LOG_FORM_DATA_ATTACHMENT] 사전 작업: incident log form-data 생성")
        response = self.client.post(
            f"/api/v1/{self.complaint_id}/evidences/incident-logs/form-data",
            json={
                "filename": "사건 일지 파일명",
                "date": "2024-01-01",
                "time": "12:00",
                "location": "서울특별시 강남구 역삼동",
                "description": "그 남자가 계속 나를 쫓아왔다",
            },
            headers=self.auth_header(),
        )
        assert response.status_code == 200, (
            "[INCIDENT_LOG_FORM_DATA_ATTACHMENT] incident log form-data 생성 실패: "
            f"status={response.status_code}, body={response.text}"
        )
        incident_log_id = str(response.json()["incident_log_id"])
        logger.info(
            "[INCIDENT_LOG_FORM_DATA_ATTACHMENT] incident_log_id 생성 완료 id=%s",
            incident_log_id,
        )
        return incident_log_id

    def request_incident_log_attachment_presigned_url(
        self, incident_log_id: str, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        logger.info(
            "[INCIDENT_LOG_FORM_DATA_ATTACHMENT] presigned-url 요청 시작 items=%s",
            len(items),
        )
        response = self.client.post(
            f"/api/v1/{self.complaint_id}/evidence/incident-log/form-data/{incident_log_id}/attachments/presigned-url",
            json={"items": items},
            headers=self.auth_header(),
        )
        assert response.status_code == 200, (
            "[INCIDENT_LOG_FORM_DATA_ATTACHMENT] presigned-url 실패: "
            f"status={response.status_code}, body={response.text}"
        )
        data = response.json()["items"]
        assert len(data) == len(items)
        logger.info("[INCIDENT_LOG_FORM_DATA_ATTACHMENT] presigned-url 요청 성공")
        return data

    def request_incident_log_attachment_register(
        self, incident_log_id: str, register_items: list[dict[str, Any]]
    ) -> httpx.Response:
        logger.info(
            "[INCIDENT_LOG_FORM_DATA_ATTACHMENT] register 요청 시작 items=%s",
            len(register_items),
        )
        response = self.client.post(
            f"/api/v1/{self.complaint_id}/evidence/incident-log/form-data/{incident_log_id}/attachments/register",
            json={"items": register_items},
            headers=self.auth_header(),
        )
        if response.status_code == 200:
            logger.info("[INCIDENT_LOG_FORM_DATA_ATTACHMENT] register 요청 성공")
        return response


class TimelineManualReferencedUploadTestRunner(BaseNoTypeRestrictUploadRunner):
    def run(self) -> None:
        logger.info("=== [TIMELINE_MANUAL_REFERENCED] 업로드 테스트 시작 ===")
        files = self.dataset_files_for_no_type_restrict()
        self.ensure_timeline_dummy_generated()
        timeline_evidence_id = self.create_manual_timeline_form_data()
        presigned_items = self.build_presigned_items(files)
        presigned_result = self.request_timeline_manual_presigned_url(
            timeline_evidence_id=timeline_evidence_id,
            items=presigned_items,
        )
        register_items = self.upload_and_build_register_items(
            files=files,
            presigned_items=presigned_result,
            register_id_field="referenced_manual_evidence_id",
        )
        register_response = self.request_timeline_manual_register(
            timeline_evidence_id=timeline_evidence_id,
            register_items=register_items,
        )
        assert register_response.status_code == 200, (
            "[TIMELINE_MANUAL_REFERENCED] register 실패: "
            f"status={register_response.status_code}, body={register_response.text}"
        )
        assert len(register_response.json()["items"]) == len(files)
        logger.info("=== [TIMELINE_MANUAL_REFERENCED] 업로드 테스트 완료 ===")

    def ensure_timeline_dummy_generated(self) -> None:
        logger.info("[TIMELINE_MANUAL_REFERENCED] 사전 작업: timeline 더미 생성 시작")
        response = self.client.get(
            f"/api/v1/{self.complaint_id}/timeline",
            params={"generate_dummy": "true"},
            headers=self.auth_header(),
        )
        assert response.status_code == 200, (
            "[TIMELINE_MANUAL_REFERENCED] timeline 더미 생성 실패: "
            f"status={response.status_code}, body={response.text}"
        )
        logger.info("[TIMELINE_MANUAL_REFERENCED] timeline 더미 생성 완료")

    def create_manual_timeline_form_data(self) -> str:
        logger.info("[TIMELINE_MANUAL_REFERENCED] 사전 작업: manual form-data 생성")
        response = self.client.post(
            f"/api/v1/{self.complaint_id}/timeline/evidences/manual/form-data",
            json={
                "date": "2026-02-12",
                "time": "14:00",
                "title": "추가 증거",
                "description": "직접 촬영한 사진",
                "tags": ["REPEAT", "THREAT_COERCION"],
            },
            headers=self.auth_header(),
        )
        assert response.status_code == 200, (
            "[TIMELINE_MANUAL_REFERENCED] manual form-data 생성 실패: "
            f"status={response.status_code}, body={response.text}"
        )
        timeline_evidence_id = str(response.json()["timeline_evidence_id"])
        logger.info(
            "[TIMELINE_MANUAL_REFERENCED] timeline_evidence_id 생성 완료 id=%s",
            timeline_evidence_id,
        )
        return timeline_evidence_id

    def request_timeline_manual_presigned_url(
        self, timeline_evidence_id: str, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        logger.info("[TIMELINE_MANUAL_REFERENCED] presigned-url 요청 시작 items=%s", len(items))
        response = self.client.post(
            f"/api/v1/{self.complaint_id}/timeline/evidences/{timeline_evidence_id}/manual/referenced-evidences/presigned-url",
            json={"items": items},
            headers=self.auth_header(),
        )
        assert response.status_code == 200, (
            "[TIMELINE_MANUAL_REFERENCED] presigned-url 실패: "
            f"status={response.status_code}, body={response.text}"
        )
        data = response.json()["items"]
        assert len(data) == len(items)
        logger.info("[TIMELINE_MANUAL_REFERENCED] presigned-url 요청 성공")
        return data

    def request_timeline_manual_register(
        self, timeline_evidence_id: str, register_items: list[dict[str, Any]]
    ) -> httpx.Response:
        logger.info("[TIMELINE_MANUAL_REFERENCED] register 요청 시작 items=%s", len(register_items))
        response = self.client.post(
            f"/api/v1/{self.complaint_id}/timeline/evidences/{timeline_evidence_id}/manual/referenced-evidences/register",
            json={"items": register_items},
            headers=self.auth_header(),
        )
        if response.status_code == 200:
            logger.info("[TIMELINE_MANUAL_REFERENCED] register 요청 성공")
        return response


def _incident_runner(
    integration_context: dict[str, str], client: Any
) -> IncidentLogAttachmentUploadTestRunner:
    return IncidentLogAttachmentUploadTestRunner(
        client=client,
        complaint_id=integration_context["complaint_id"],
        access_token=integration_context["access_token"],
        dataset_root=DATASET_ROOT_DIR,
    )


def _timeline_runner(
    integration_context: dict[str, str], client: Any
) -> TimelineManualReferencedUploadTestRunner:
    return TimelineManualReferencedUploadTestRunner(
        client=client,
        complaint_id=integration_context["complaint_id"],
        access_token=integration_context["access_token"],
        dataset_root=DATASET_ROOT_DIR,
    )


def test_incident_log_form_data_attachment_upload_success(
    integration_context: dict[str, str], client: Any
):
    _incident_runner(integration_context, client).run()


def test_timeline_manual_referenced_evidence_upload_success(
    integration_context: dict[str, str], client: Any
):
    _timeline_runner(integration_context, client).run()
