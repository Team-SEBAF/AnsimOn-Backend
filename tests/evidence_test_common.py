import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CONTENT_TYPE_MAP: dict[str, str] = {
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


@dataclass(frozen=True)
class EvidenceApiSpec:
    evidence_type: str
    dataset_dir_name: str
    register_path_suffix: str
    register_id_field: str


class BaseEvidenceRunner:
    def __init__(self, client: Any, complaint_id: str, access_token: str, dataset_root: Path):
        self.client = client
        self.complaint_id = complaint_id
        self.access_token = access_token
        self.dataset_root = dataset_root

    def dataset_files(self, spec: EvidenceApiSpec, label: str = "테스트") -> list[Path]:
        target_dir = self.dataset_root / spec.dataset_dir_name
        files = sorted([path for path in target_dir.iterdir() if path.is_file()])
        assert files, f"[{spec.evidence_type}] {label} 파일이 없습니다. dir={target_dir}"
        logger.info("[%s] %s 파일 개수=%s", spec.evidence_type, label, len(files))
        return files

    def build_presigned_items(self, files: list[Path]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for index, file_path in enumerate(files):
            content_type = self.content_type(file_path)
            item: dict[str, Any] = {
                "index": index,
                "filename": file_path.name,
                "contentType": content_type,
                "sizeBytes": file_path.stat().st_size,
            }
            if self._requires_duration(content_type):
                duration = self.duration_seconds(file_path)
                assert duration is not None, f"duration 추출 실패: file={file_path.name}"
                item["durationSeconds"] = duration
            items.append(item)
        return items

    def request_presigned_url(
        self, spec: EvidenceApiSpec, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        logger.info("[%s] (1) presigned-url 요청 시작 items=%s", spec.evidence_type, len(items))
        response = self.client.post(
            f"/api/v1/evidences/{self.complaint_id}/presigned-url",
            json={"type": spec.evidence_type, "items": items},
            headers=self.auth_header(),
        )
        assert response.status_code == 200, (
            f"[{spec.evidence_type}] presigned-url 실패: "
            f"status={response.status_code}, body={response.text}"
        )
        data = response.json()["items"]
        assert len(data) == len(items)
        logger.info("[%s] (1) presigned-url 요청 성공", spec.evidence_type)
        return data

    def upload_and_build_register_items(
        self, spec: EvidenceApiSpec, files: list[Path], presigned_items: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[str]]:
        items_by_index = {item["index"]: item for item in presigned_items}
        register_items: list[dict[str, Any]] = []
        requested_evidence_ids: list[str] = []

        logger.info("[%s] (2) presigned-url로 파일 업로드 시작", spec.evidence_type)
        for index, file_path in enumerate(files):
            presigned_item = items_by_index[index]
            logger.info(
                "[%s] 파일 업로드 중 index=%s name=%s", spec.evidence_type, index, file_path.name
            )
            upload_response = httpx.put(
                presigned_item["url"],
                content=file_path.read_bytes(),
                headers={"Content-Type": self.content_type(file_path)},
                timeout=60.0,
            )
            assert upload_response.status_code == 200, (
                f"[{spec.evidence_type}] 파일 업로드 실패: "
                f"file={file_path.name}, status={upload_response.status_code}, "
                f"body={upload_response.text}"
            )
            logger.info(
                "[%s] 파일 업로드 성공 index=%s name=%s", spec.evidence_type, index, file_path.name
            )

            evidence_id = str(presigned_item["evidence_id"])
            requested_evidence_ids.append(evidence_id)
            register_items.append(
                {
                    spec.register_id_field: presigned_item["evidence_id"],
                    "filename": file_path.name,
                    "fileCreatedAt": self.file_created_at(file_path),
                }
            )

        return register_items, requested_evidence_ids

    def request_register(
        self, spec: EvidenceApiSpec, register_items: list[dict[str, Any]]
    ) -> httpx.Response:
        logger.info("[%s] (3) register 요청 시작 items=%s", spec.evidence_type, len(register_items))
        response = self.client.post(
            f"/api/v1/{self.complaint_id}/{spec.register_path_suffix}",
            json={"items": register_items},
            headers=self.auth_header(),
        )
        if response.status_code == 200:
            logger.info("[%s] (3) register 요청 성공", spec.evidence_type)
        return response

    def auth_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    @staticmethod
    def file_created_at(file_path: Path) -> str:
        return datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()

    @staticmethod
    def duration_seconds(file_path: Path) -> int | None:
        del file_path
        # presigned-url 단계는 duration 값 자체만 검증하므로 테스트에서는 고정값 사용
        return 60

    @staticmethod
    def content_type(file_path: Path) -> str:
        content_type = CONTENT_TYPE_MAP.get(file_path.suffix.lower())
        if content_type is None:
            raise ValueError(f"지원하지 않는 파일 타입입니다: {file_path.name}")
        return content_type

    @staticmethod
    def _requires_duration(content_type: str) -> bool:
        return content_type.startswith("audio/") or content_type.startswith("video/")
