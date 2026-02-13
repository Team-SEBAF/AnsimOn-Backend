import datetime
from uuid import UUID

from pydantic import Field

from app.base.base_response import BaseResponse
from app.domain.evidence.constant import EVIDENCE_DOCUMENT_RESTRICT


class EvidenceIncidentLogFileResponse(BaseResponse):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="사건 일지 파일명", examples=["사건 일지 파일명"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    created_at: datetime.datetime = Field(
        ...,
        description="생성 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )
    updated_at: datetime.datetime = Field(
        ...,
        description="수정 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )


class EvidenceIncidentLogFileUploadResponse(BaseResponse):
    incident_log_files: list[EvidenceIncidentLogFileResponse] = Field(
        ..., description="업로드된 사건 일지 파일 목록"
    )
    type_invalid_filenames: list[str] = Field(
        ...,
        description=f"가능한 신고・사건 일지 타입({EVIDENCE_DOCUMENT_RESTRICT.allowed_types})이 아니라 거절된 파일명 목록",
        examples=["evidence.pdf"],
    )
    count_invalid_filenames: list[str] = Field(
        ...,
        description=f"최대 개수 {EVIDENCE_DOCUMENT_RESTRICT.max_count}개를 초과하여 거절된 파일명 목록",
        examples=["evidence.mp3"],
    )
    size_invalid_filenames: list[str] = Field(
        ...,
        description=f"파일 크기가 {EVIDENCE_DOCUMENT_RESTRICT.max_size_bytes / 1024 / 1024}MB를 초과하여 거절된 파일명 목록",
        examples=["evidence.mp3"],
    )


class EvidenceIncidentLogFormDataResponse(BaseResponse):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    name: str = Field(..., description="사건 일지 이름", examples=["사건 일지 이름"])
    date: datetime.date = Field(
        ..., description="날짜(YYYY-MM-DD)", examples=[datetime.date(2024, 1, 1)]
    )
    time: datetime.time = Field(..., description="시간(HH:MM)", examples=[datetime.time(12, 0, 0)])
    location: str = Field(..., description="장소", examples=["서울특별시 강남구 역삼동"])
    description: str = Field(..., description="설명", examples=["그 남자가 계속 나를 쫓아왔다"])
    witness: str = Field(..., description="목격자", examples=["주변 사람"])
    perceived_risk: str = Field(
        ...,
        description="느낀 위험 정도",
        examples=["매우 높음", "높음", "보통", "낮음", "매우 낮음"],
    )
    created_at: datetime.datetime = Field(
        ...,
        description="생성 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )
    updated_at: datetime.datetime = Field(
        ...,
        description="수정 시간",
        examples=[datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)],
    )


class EvidenceIncidentLogFileOriginalResponse(BaseResponse):
    incident_log_id: UUID = Field(
        ..., description="사건 일지 ID", examples=[UUID("123e4567-e89b-12d3-a456-426614174000")]
    )
    filename: str = Field(..., description="사건 일지 파일명", examples=["사건 일지 파일명"])
    content_type: str = Field(..., description="Content-Type", examples=["application/pdf"])
    size_bytes: int = Field(..., description="파일 크기(바이트)", examples=[12345])
    url: str = Field(..., description="원본 사건 일지 파일 URL", examples=["https://..."])
