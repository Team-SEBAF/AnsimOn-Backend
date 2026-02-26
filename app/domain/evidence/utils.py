from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar
from uuid import UUID

from app.base.base_error import CodeException
from app.core.aws import head_s3_object
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence.constant import EvidenceTypeRestrict
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.errors.s3_not_uploaded_yet_error import (
    S3NotUploadedYetErrorCode,
)

T = TypeVar("T")


def check_register_max_count(
    total_count: int,
    request_count: int,
    restrict: EvidenceTypeRestrict,
    type_name: str,
) -> None:
    """total_count + request_count가 restrict.max_count 초과 시 CodeException raise."""
    if total_count + request_count > restrict.max_count:
        raise CodeException(
            code=EvidenceMaxCountExceededErrorCode.EVIDENCE_MAX_COUNT_EXCEEDED,
            message="해당 증거 타입의 최대 개수를 초과했습니다.",
            debug_message=f"{type_name} 타입 증거의 최대 개수({restrict.max_count}개)를 초과합니다. (현재 {total_count}개 + 요청 {request_count}개)",
            status_code=400,
        )


def validate_s3_uploads_before_register(
    complaint: Complaint,
    items: list[T],
    path_segment: str,
    get_evidence_id: Callable[[T], UUID],
) -> None:
    """S3에 업로드되지 않은 항목이 있으면 CodeException raise."""

    def _check(item: T) -> UUID | None:
        s3_key = (
            f"{complaint.user_sub}/complaints/"
            f"{complaint.complaint_id}/evidences/{path_segment}/{get_evidence_id(item)}/original"
        )
        return (
            get_evidence_id(item)
            if head_s3_object(settings.S3_BUCKET_NAME, s3_key) is None
            else None
        )

    with ThreadPoolExecutor(max_workers=max(1, min(len(items), 5))) as executor:
        failed_ids = [eid for eid in executor.map(_check, items) if eid is not None]

    if failed_ids:
        raise CodeException(
            code=S3NotUploadedYetErrorCode.S3_NOT_UPLOADED_YET,
            message="에러가 발생하여 작업이 중단되었습니다. 잠시 후 다시 시도해 주세요.",
            debug_message="S3에 파일이 업로드되지 않은 증거가 있습니다. 먼저 presigned URL로 업로드해 주세요.",
            status_code=400,
            detail={"failed_evidence_ids": [str(eid) for eid in failed_ids]},
        )


def fetch_s3_metadata_for_register(
    complaint: Complaint,
    items: list[T],
    path_segment: str,
    get_evidence_id: Callable[[T], UUID],
    build_extra: Callable[[T, str, str, int], dict] | None = None,
) -> list[dict]:
    """
    S3 head_object로 content_type, size_bytes 조회.
    없으면 S3_NOT_UPLOADED_YET raise. 반환: list of {evidence_id, s3_key, content_type, size_bytes, ...extra}
    """

    def _fetch(item: T) -> tuple[dict | None, UUID | None]:
        eid = get_evidence_id(item)
        s3_key = (
            f"{complaint.user_sub}/complaints/"
            f"{complaint.complaint_id}/evidences/{path_segment}/{eid}/original"
        )
        meta = head_s3_object(settings.S3_BUCKET_NAME, s3_key)
        if meta is None:
            return None, eid
        raw_ct = meta.get("ContentType") or "application/octet-stream"
        content_type = raw_ct.split(";")[0].strip().lower()
        size_bytes = meta.get("ContentLength") or 0
        row: dict = {
            "evidence_id": eid,
            "s3_key": s3_key,
            "content_type": content_type,
            "size_bytes": size_bytes,
        }
        if build_extra:
            row.update(build_extra(item, s3_key, content_type, size_bytes))
        return row, None

    with ThreadPoolExecutor(max_workers=max(1, min(len(items), 5))) as executor:
        results = list(executor.map(_fetch, items))

    failed_ids = [eid for _, eid in results if eid is not None]
    if failed_ids:
        raise CodeException(
            code=S3NotUploadedYetErrorCode.S3_NOT_UPLOADED_YET,
            message="에러가 발생하여 작업이 중단되었습니다. 잠시 후 다시 시도해 주세요.",
            debug_message="S3에 파일이 업로드되지 않은 증거가 있습니다. 먼저 presigned URL로 업로드해 주세요.",
            status_code=400,
            detail={"failed_evidence_ids": [str(eid) for eid in failed_ids]},
        )

    return [r for r, _ in results]
