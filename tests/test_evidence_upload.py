import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from mutagen import File as MutagenFile

DATASET_ROOT_DIR = Path(__file__).resolve().parent / "integration_test_set" / "evidence_upload_test"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvidenceUploadSpec:
    evidence_type: str
    dataset_dir_name: str
    register_path_suffix: str
    register_id_field: str


class EvidenceUploadTestRunner:
    def __init__(self, client: Any, complaint_id: str, access_token: str):
        self.client = client
        self.complaint_id = complaint_id
        self.access_token = access_token

    def run(self, spec: EvidenceUploadSpec) -> None:
        logger.info("=== [%s] 업로드 테스트 시작 ===", spec.evidence_type)
        files = self._dataset_files(spec)
        logger.info("[%s] 테스트 파일 개수=%s", spec.evidence_type, len(files))
        presigned_items = self._build_presigned_items(files)
        presigned_result = self._request_presigned_url(spec, presigned_items)
        register_items = self._upload_files_and_build_register_items(spec, files, presigned_result)
        self._request_register(spec, register_items)
        logger.info("=== [%s] 업로드 테스트 완료 ===", spec.evidence_type)

    def _dataset_files(self, spec: EvidenceUploadSpec) -> list[Path]:
        target_dir = DATASET_ROOT_DIR / spec.dataset_dir_name
        files = sorted([path for path in target_dir.iterdir() if path.is_file()])
        assert files, f"[{spec.evidence_type}] 테스트 파일이 없습니다. dir={target_dir}"
        return files

    def _build_presigned_items(self, files: list[Path]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for index, file_path in enumerate(files):
            item: dict[str, Any] = {
                "index": index,
                "filename": file_path.name,
                "contentType": self._content_type(file_path),
                "sizeBytes": file_path.stat().st_size,
            }
            duration = self._duration_seconds(file_path)
            if duration is not None:
                item["durationSeconds"] = duration
            items.append(item)
        return items

    def _request_presigned_url(
        self, spec: EvidenceUploadSpec, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        logger.info("[%s] (1) presigned-url 요청 시작 items=%s", spec.evidence_type, len(items))
        response = self.client.post(
            f"/api/v1/evidences/{self.complaint_id}/presigned-url",
            json={"type": spec.evidence_type, "items": items},
            headers=self._auth_header(),
        )
        assert response.status_code == 200, (
            f"[{spec.evidence_type}] presigned-url 실패: "
            f"status={response.status_code}, body={response.text}"
        )
        data = response.json()["items"]
        assert len(data) == len(items)
        return data

    def _upload_files_and_build_register_items(
        self, spec: EvidenceUploadSpec, files: list[Path], presigned_items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        items_by_index = {item["index"]: item for item in presigned_items}
        register_items: list[dict[str, Any]] = []

        logger.info("[%s] (2) presigned-url로 파일 업로드 시작", spec.evidence_type)
        for index, file_path in enumerate(files):
            presigned_item = items_by_index[index]
            logger.info(
                "[%s] 파일 업로드 중 index=%s name=%s",
                spec.evidence_type,
                index,
                file_path.name,
            )
            upload_response = httpx.put(
                presigned_item["url"],
                content=file_path.read_bytes(),
                headers={"Content-Type": self._content_type(file_path)},
                timeout=60.0,
            )
            assert upload_response.status_code == 200, (
                f"[{spec.evidence_type}] 파일 업로드 실패: "
                f"file={file_path.name}, status={upload_response.status_code}, "
                f"body={upload_response.text}"
            )
            logger.info(
                "[%s] 파일 업로드 성공 index=%s name=%s",
                spec.evidence_type,
                index,
                file_path.name,
            )

            register_items.append(
                {
                    spec.register_id_field: presigned_item["evidence_id"],
                    "filename": file_path.name,
                    "fileCreatedAt": self._file_created_at(file_path),
                }
            )

        return register_items

    def _request_register(
        self, spec: EvidenceUploadSpec, register_items: list[dict[str, Any]]
    ) -> None:
        logger.info("[%s] (3) register 요청 시작 items=%s", spec.evidence_type, len(register_items))
        response = self.client.post(
            f"/api/v1/{self.complaint_id}/{spec.register_path_suffix}",
            json={"items": register_items},
            headers=self._auth_header(),
        )
        assert response.status_code == 200, (
            f"[{spec.evidence_type}] register 실패: "
            f"status={response.status_code}, body={response.text}"
        )
        logger.info("[%s] (3) register 요청 성공", spec.evidence_type)

    def _auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    @staticmethod
    def _file_created_at(file_path: Path) -> str:
        return datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()

    @staticmethod
    def _duration_seconds(file_path: Path) -> int | None:
        if file_path.suffix.lower() not in {".mp3", ".wav", ".m4a", ".mp4", ".mov"}:
            return None
        parsed = MutagenFile(file_path)
        assert (
            parsed is not None and getattr(parsed, "info", None) is not None
        ), f"duration 추출 실패: file={file_path.name}"
        length = int(getattr(parsed.info, "length", 0))
        return max(1, length)

    @staticmethod
    def _content_type(file_path: Path) -> str:
        suffix = file_path.suffix.lower()
        content_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".heic": "image/heic",
            ".m4a": "audio/mp4",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain",
        }
        content_type = content_type_map.get(suffix)
        if content_type is None:
            raise ValueError(f"Unsupported file type: {file_path.name}")
        return content_type


def _runner(integration_context: dict[str, str], client: Any) -> EvidenceUploadTestRunner:
    return EvidenceUploadTestRunner(
        client=client,
        complaint_id=integration_context["complaint_id"],
        access_token=integration_context["access_token"],
    )


def test_evidence_upload_message_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceUploadSpec(
            evidence_type="MESSAGE",
            dataset_dir_name="MESSAGE",
            register_path_suffix="evidences/messages/register",
            register_id_field="messageId",
        )
    )


def test_evidence_upload_voice_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceUploadSpec(
            evidence_type="VOICE",
            dataset_dir_name="VOICE",
            register_path_suffix="evidences/voices/register",
            register_id_field="voiceId",
        )
    )


def test_evidence_upload_victim_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceUploadSpec(
            evidence_type="VICTIM",
            dataset_dir_name="VICTIM",
            register_path_suffix="evidences/victims/register",
            register_id_field="victimId",
        )
    )


def test_evidence_upload_report_record_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceUploadSpec(
            evidence_type="REPORT_RECORD",
            dataset_dir_name="REPORT_RECORD",
            register_path_suffix="evidences/report-records/register",
            register_id_field="reportRecordId",
        )
    )


def test_evidence_upload_incident_log_success(integration_context: dict[str, str], client: Any):
    _runner(integration_context, client).run(
        EvidenceUploadSpec(
            evidence_type="INCIDENT_LOG",
            dataset_dir_name="INCIDENT_LOG",
            register_path_suffix="evidences/incident-logs/file/register",
            register_id_field="incidentLogId",
        )
    )
