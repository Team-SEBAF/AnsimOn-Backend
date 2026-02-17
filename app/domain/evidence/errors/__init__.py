from pydantic import Field

from app.base.base_error import BaseErrorResponse

from .evidence_max_count_exceeded_error import (
    EVIDENCE_MAX_COUNT_EXCEEDED_ERRORS_RESPONSES,
    EvidenceMaxCountExceededErrorCode,
)
from .get_evidence_error import GET_EVIDENCE_ERRORS_RESPONSES, GetEvidenceErrorCode
from .register_validation_error import (
    EVIDENCE_REGISTER_VALIDATION_FAILED_ERRORS_RESPONSES,
    EvidenceRegisterValidationErrorCode,
    EvidenceRegisterValidationErrorResponse,
)
from .s3_not_uploaded_yet_error import (
    S3_NOT_UPLOADED_YET_ERRORS_RESPONSES,
    S3NotUploadedYetErrorCode,
)


class RegisterEvidenceErrorResponse(BaseErrorResponse):
    """register 엔드포인트 400 에러. S3_NOT_UPLOADED_YET 시 failed_evidence_ids 포함."""

    failed_evidence_ids: list[str] = Field(
        default_factory=list,
        description="S3에 업로드되지 않은 evidence_id 목록",
    )


REGISTER_EVIDENCE_ERRORS_RESPONSES = {
    400: {
        "model": RegisterEvidenceErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    **EVIDENCE_MAX_COUNT_EXCEEDED_ERRORS_RESPONSES[400]["content"][
                        "application/json"
                    ]["examples"],
                    **S3_NOT_UPLOADED_YET_ERRORS_RESPONSES[400]["content"]["application/json"][
                        "examples"
                    ],
                    **EVIDENCE_REGISTER_VALIDATION_FAILED_ERRORS_RESPONSES[400]["content"][
                        "application/json"
                    ]["examples"],
                }
            }
        },
    },
}

__all__ = [
    "EVIDENCE_MAX_COUNT_EXCEEDED_ERRORS_RESPONSES",
    "EvidenceMaxCountExceededErrorCode",
    "EVIDENCE_REGISTER_VALIDATION_FAILED_ERRORS_RESPONSES",
    "EvidenceRegisterValidationErrorCode",
    "EvidenceRegisterValidationErrorResponse",
    "GET_EVIDENCE_ERRORS_RESPONSES",
    "GetEvidenceErrorCode",
    "REGISTER_EVIDENCE_ERRORS_RESPONSES",
    "S3_NOT_UPLOADED_YET_ERRORS_RESPONSES",
    "S3NotUploadedYetErrorCode",
]
