from enum import Enum

from pydantic import Field

from app.base.base_error import BaseErrorResponse, CodeException


class EvidenceRegisterValidationErrorCode(str, Enum):
    """
    Register 검증 에러 코드 (Phase 2: restrict 검증)

    - EVIDENCE_REGISTER_VALIDATION_FAILED: content_type/size_bytes/duration 검증 실패
    """

    EVIDENCE_REGISTER_VALIDATION_FAILED = "EVIDENCE_REGISTER_VALIDATION_FAILED"


class EvidenceRegisterValidationErrorResponse(BaseErrorResponse):
    code: EvidenceRegisterValidationErrorCode
    message: str
    content_type_failed_evidence_ids: list[str] = Field(
        default_factory=list,
        description="content_type 검사 실패한 evidence_id 목록",
    )
    size_bytes_failed_evidence_ids: list[str] = Field(
        default_factory=list,
        description="size_bytes 검사 실패한 evidence_id 목록",
    )
    duration_seconds_failed_evidence_ids: list[str] | None = Field(
        default=None,
        description="duration_seconds 검사 실패한 evidence_id 목록 (VOICE, TRACKING 타입일 때만 포함)",
    )


def raise_evidence_register_validation_failed(
    content_type_failed_evidence_ids: list[str],
    size_bytes_failed_evidence_ids: list[str],
    duration_seconds_failed_evidence_ids: list[str] | None = None,
) -> None:
    """content_type 먼저 검사, 통과한 것만 size/duration. content_type 걸린 건 size/duration에 포함 안 함."""
    if not (
        content_type_failed_evidence_ids
        or size_bytes_failed_evidence_ids
        or (duration_seconds_failed_evidence_ids or [])
    ):
        return
    detail: dict = {
        "content_type_failed_evidence_ids": content_type_failed_evidence_ids,
        "size_bytes_failed_evidence_ids": size_bytes_failed_evidence_ids,
    }
    if duration_seconds_failed_evidence_ids is not None:
        detail["duration_seconds_failed_evidence_ids"] = duration_seconds_failed_evidence_ids
    raise CodeException(
        code=EvidenceRegisterValidationErrorCode.EVIDENCE_REGISTER_VALIDATION_FAILED,
        message="증거 유효성 검사에 통과하지 못한 증거가 존재하여 작업이 중단되었습니다. failed_evidence_ids를 확인해 주세요.",
        status_code=400,
        detail=detail,
    )


EVIDENCE_REGISTER_VALIDATION_FAILED_ERRORS_RESPONSES = {
    400: {
        "model": EvidenceRegisterValidationErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "EVIDENCE_REGISTER_VALIDATION_FAILED": {
                        "summary": "restrict 검증 실패 (content_type/size_bytes/duration)",
                        "value": {
                            "code": "EVIDENCE_REGISTER_VALIDATION_FAILED",
                            "message": "증거 파일이 제한 조건을 충족하지 않습니다. failed_evidence_ids를 확인해 주세요.",
                            "content_type_failed_evidence_ids": [],
                            "size_bytes_failed_evidence_ids": [],
                            "duration_seconds_failed_evidence_ids": [],
                        },
                    }
                }
            }
        },
    },
}
