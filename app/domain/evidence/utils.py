from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar
from uuid import UUID, uuid4

from app.base.base_error import CodeException
from app.core.aws import generate_presigned_put_url, head_s3_object
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence.constant import (
    EVIDENCE_DOCUMENT_RESTRICT,
    EVIDENCE_IMAGE_RESTRICT,
    EVIDENCE_VIDEO_RESTRICT,
    EVIDENCE_VOICE_AUDIO_RESTRICT,
    EvidenceTypeRestrict,
    MediaTypeRestrict,
)
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.errors.presigned_validation_error import (
    EvidencePresignedValidationErrorCode,
)
from app.domain.evidence.errors.s3_not_uploaded_yet_error import (
    S3NotUploadedYetErrorCode,
)
from app.domain.evidence.schemas.common import EvidencePresignedUrlItemRequest

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


def get_restrict_by_content_type(
    content_type: str,
) -> EvidenceTypeRestrict | MediaTypeRestrict:
    """
    content_type별 restrict 반환. 타입 제한 없을 때(첨부/수동 증거) size/duration만 기존 constant와 동일 적용.
    """
    if content_type in EVIDENCE_VIDEO_RESTRICT.allowed_types:
        return EVIDENCE_VIDEO_RESTRICT
    if content_type in EVIDENCE_IMAGE_RESTRICT.allowed_types:
        return EVIDENCE_IMAGE_RESTRICT
    if content_type in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types:
        return EVIDENCE_VOICE_AUDIO_RESTRICT
    if content_type in EVIDENCE_DOCUMENT_RESTRICT.allowed_types:
        return EVIDENCE_DOCUMENT_RESTRICT
    return EVIDENCE_DOCUMENT_RESTRICT  # 알 수 없는 타입: 10MB 기본


def generate_presigned_urls_for_unrestricted_content(
    complaint: Complaint,
    items: list[EvidencePresignedUrlItemRequest],
    s3_key_builder: Callable[[Complaint, UUID], str],
    id_field_name: str = "id",
) -> list[dict]:
    """
    content_type 제한 없는 첨부/수동 증거용 Presigned URL 발급.
    size/duration 검증 후 각 item에 대해 uuid 생성, presigned URL 발급.
    Returns: list of {index, filename, url, <id_field_name>: UUID}
    """
    size_bytes_failed_index_list: list[int] = []
    duration_seconds_failed_index_list: list[int] = []
    for item in items:
        r = get_restrict_by_content_type(item.content_type)
        if item.size_bytes > r.max_size_bytes:
            size_bytes_failed_index_list.append(item.index)
        if r.max_duration_seconds is not None and (
            item.duration_seconds is None or item.duration_seconds > r.max_duration_seconds
        ):
            duration_seconds_failed_index_list.append(item.index)
    if size_bytes_failed_index_list or duration_seconds_failed_index_list:
        detail: dict = {"size_bytes_failed_index_list": size_bytes_failed_index_list}
        if duration_seconds_failed_index_list:
            detail["duration_seconds_failed_index_list"] = duration_seconds_failed_index_list
        raise CodeException(
            code=EvidencePresignedValidationErrorCode.EVIDENCE_PRESIGNED_VALIDATION_FAILED,
            message="증거 유효성 검사에 통과하지 못한 증거가 존재하여 작업이 중단되었습니다.",
            debug_message="증거 유효성 검사에 통과하지 못한 증거가 존재하여 presigned URL 발급이 중단되었습니다. failed_index_list를 확인해주세요.",
            status_code=400,
            detail=detail,
        )
    result = []
    for item in items:
        eid = uuid4()
        s3_key = s3_key_builder(complaint, eid)
        url = generate_presigned_put_url(
            bucket=settings.S3_BUCKET_NAME,
            key=s3_key,
            content_type=item.content_type,
            expires_in=600,
        )
        row: dict = {"index": item.index, "filename": item.filename, "url": url}
        row[id_field_name] = eid
        result.append(row)
    return result


def fetch_s3_metadata_for_register(
    complaint: Complaint,
    items: list[T],
    path_segment: str,
    get_evidence_id: Callable[[T], UUID],
    build_extra: Callable[[T, str, str, int], dict] | None = None,
    path_prefix: str = "evidences",
) -> list[dict]:
    """
    S3 head_object로 content_type, size_bytes 조회.
    없으면 S3_NOT_UPLOADED_YET raise. 반환: list of {evidence_id, s3_key, content_type, size_bytes, ...extra}
    path_prefix: "evidences" | "timeline" 등. 기본 evidences.
    """

    def _fetch(item: T) -> tuple[dict | None, UUID | None]:
        eid = get_evidence_id(item)
        s3_key = (
            f"{complaint.user_sub}/complaints/"
            f"{complaint.complaint_id}/{path_prefix}/{path_segment}/{eid}/original"
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
