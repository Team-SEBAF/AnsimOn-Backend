from enum import Enum

from pydantic import Field

from app.base.base_error import BaseErrorResponse


class EvidencePresignedValidationErrorCode(str, Enum):
    """
    Presigned URL 발급 검증 에러 코드

    - EVIDENCE_PRESIGNED_VALIDATION_FAILED: 검증 실패 (detail에 실패 항목별 인덱스 포함)
    """

    EVIDENCE_PRESIGNED_VALIDATION_FAILED = "EVIDENCE_PRESIGNED_VALIDATION_FAILED"


class EvidencePresignedValidationErrorResponse(BaseErrorResponse):
    code: EvidencePresignedValidationErrorCode
    message: str
    is_total_count_valid: bool = Field(
        default=True,
        description="total_count 검사 통과 여부",
    )
    content_type_failed_index_list: list[int] = Field(
        default_factory=list,
        description="content_type 검사 실패한 item index 목록",
    )
    size_bytes_failed_index_list: list[int] = Field(
        default_factory=list,
        description="size_bytes 검사 실패한 item index 목록",
    )
    duration_seconds_failed_index_list: list[int] | None = Field(
        default=None,
        description="duration_seconds 검사 실패한 item index 목록 (VOICE, TRACKING 타입일 때만 포함)",
    )


EVIDENCE_PRESIGNED_VALIDATION_ERRORS_RESPONSES = {
    400: {
        "model": EvidencePresignedValidationErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "EVIDENCE_PRESIGNED_VALIDATION_FAILED": {
                        "summary": "증거 유효성 검사 실패 (fail 결과 확인)",
                        "value": {
                            "code": "EVIDENCE_PRESIGNED_VALIDATION_FAILED",
                            "message": "증거 유효성 검사에 통과하지 못한 증거가 존재하여 presigned URL 발급이 중단되었습니다. failed_index_list를 확인해주세요.",
                            "is_total_count_valid": True,
                            "content_type_failed_index_list": [0, 2],
                            "size_bytes_failed_index_list": [1],
                            "duration_seconds_failed_index_list": [0],
                        },
                    },
                }
            }
        },
    },
}
