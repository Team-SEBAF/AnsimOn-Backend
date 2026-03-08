from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set


@dataclass(frozen=True)
class EvidenceTypeRestrict:
    allowed_types: Set[str]
    max_count: int
    max_size_bytes: int
    max_duration_seconds: Optional[int] = None


@dataclass(frozen=True)
class MediaTypeRestrict:
    """타입별(영상/이미지) 제한. max_count는 Evidence 단위(EVIDENCE_VICTIM_RESTRICT)에서만."""

    allowed_types: Set[str]
    max_size_bytes: int
    max_duration_seconds: Optional[int] = None


EVIDENCE_IMAGE_RESTRICT = EvidenceTypeRestrict(
    allowed_types={
        "image/jpeg",
        "image/png",
        "image/heic",
        "image/heif",
    },
    max_count=10,
    max_size_bytes=10 * 1024 * 1024,  # 10MB / 파일
)

EVIDENCE_MESSAGE_RESTRICT = EVIDENCE_IMAGE_RESTRICT

EVIDENCE_VOICE_RESTRICT = EvidenceTypeRestrict(
    allowed_types={
        "audio/mp4",  # m4a
        "audio/x-m4a",
        "audio/mpeg",  # mp3
        "audio/wav",
        "audio/x-wav",
    },
    max_count=5,
    max_size_bytes=20 * 1024 * 1024,  # 20MB
    max_duration_seconds=300,  # 5분
)

# VICTIM: 영상 + 이미지. max_count는 EVIDENCE_VICTIM_RESTRICT에만.
EVIDENCE_VICTIM_VIDEO_RESTRICT = MediaTypeRestrict(
    allowed_types={"video/mp4", "video/quicktime"},
    max_size_bytes=500 * 1024 * 1024,  # 500MB
    max_duration_seconds=300,  # 5분
)

EVIDENCE_VICTIM_IMAGE_RESTRICT = MediaTypeRestrict(
    allowed_types=EVIDENCE_IMAGE_RESTRICT.allowed_types,
    max_size_bytes=EVIDENCE_IMAGE_RESTRICT.max_size_bytes,  # 10MB, MESSAGE와 동일
)

EVIDENCE_VICTIM_RESTRICT = EvidenceTypeRestrict(
    allowed_types=EVIDENCE_VICTIM_VIDEO_RESTRICT.allowed_types
    | EVIDENCE_VICTIM_IMAGE_RESTRICT.allowed_types,
    max_count=3,
    max_size_bytes=0,  # presigned/register에서 타입별 EVIDENCE_VICTIM_VIDEO/IMAGE_RESTRICT 사용
    max_duration_seconds=None,
)

EVIDENCE_DOCUMENT_RESTRICT = EvidenceTypeRestrict(
    allowed_types={
        # PDF
        "application/pdf",
        # Word
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        # HWP (windows only)
        "application/x-hwp",
        "application/haansofthwp",
        "application/vnd.hancom.hwp",
        # TXT
        "text/plain",
    },
    max_count=3,
    max_size_bytes=10 * 1024 * 1024,  # 10MB
)


class EvidenceType(str, Enum):
    """증거 타입

    MESSAGE: 메신저, 문자, DM
    VOICE: 통화, 음성
    VICTIM: 피해 사진/영상
    INCIDENT_LOG: 신고, 상담 기록
    REPORT_RECORD: 사건 일지
    """

    MESSAGE = "MESSAGE"
    VOICE = "VOICE"
    VICTIM = "VICTIM"
    REPORT_RECORD = "REPORT_RECORD"
    INCIDENT_LOG = "INCIDENT_LOG"


class EvidenceVariant(str, Enum):
    THUMBNAIL = "thumbnail"
    DETAIL = "detail"
    ORIGINAL = "original"
