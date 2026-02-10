from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set


@dataclass(frozen=True)
class EvidenceTypeRestrict:
    allowed_types: Set[str]
    max_count: int
    max_size_bytes: int
    max_duration_seconds: Optional[int] = None


EVIDENCE_MESSAGE_RESTRICT = EvidenceTypeRestrict(
    allowed_types={
        "image/jpeg",
        "image/png",
        "image/heic",
        "image/heif",
    },
    max_count=10,
    max_size_bytes=10 * 1024 * 1024,  # 10MB / 파일
)

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

EVIDENCE_TRACKING_RESTRICT = EvidenceTypeRestrict(
    allowed_types={
        "video/mp4",
        "video/quicktime",  # mov
    },
    max_count=3,
    max_size_bytes=500 * 1024 * 1024,  # 500MB
    max_duration_seconds=300,  # 5분
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


class EvidenceMessageVariant(str, Enum):
    THUMBNAIL = "thumbnail"
    DETAIL = "detail"
    ORIGINAL = "original"
