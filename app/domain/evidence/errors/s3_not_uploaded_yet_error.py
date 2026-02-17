from enum import Enum

from pydantic import Field

from app.base.base_error import BaseErrorResponse


class S3NotUploadedYetErrorCode(str, Enum):
    """
    S3 업로드 전 register 호출 에러 코드

    - S3_NOT_UPLOADED_YET: presigned URL로 S3 업로드를 하지 않은 상태에서 register 호출
    """

    S3_NOT_UPLOADED_YET = "S3_NOT_UPLOADED_YET"


class S3NotUploadedYetErrorResponse(BaseErrorResponse):
    code: S3NotUploadedYetErrorCode
    message: str
    failed_evidence_ids: list[str] = Field(
        default_factory=list,
        description="S3에 업로드되지 않은 evidence_id 목록 (배치 register 시)",
    )


S3_NOT_UPLOADED_YET_ERRORS_RESPONSES = {
    400: {
        "model": S3NotUploadedYetErrorResponse,
        "content": {
            "application/json": {
                "examples": {
                    "S3_NOT_UPLOADED_YET": {
                        "summary": "S3에 파일이 업로드되지 않았습니다.",
                        "value": {
                            "code": "S3_NOT_UPLOADED_YET",
                            "message": "S3에 파일이 업로드되지 않았습니다. 먼저 presigned URL로 업로드해 주세요.",
                            "failed_evidence_ids": [
                                "123e4567-e89b-12d3-a456-426614174000",
                                "223e4567-e89b-12d3-a456-426614174001",
                            ],
                        },
                    }
                }
            }
        },
    },
}
