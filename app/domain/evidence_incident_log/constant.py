from enum import Enum

from app.domain.evidence.constant import (
    EVIDENCE_DOCUMENT_RESTRICT,
    EVIDENCE_IMAGE_RESTRICT,
    EVIDENCE_VIDEO_RESTRICT,
    EVIDENCE_VOICE_AUDIO_RESTRICT,
)


class FormDataAttachmentType(str, Enum):
    """첨부 자료 미디어 타입. content_type 기반 분류."""

    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"
    ETC = "ETC"


def get_attachment_type_from_content_type(content_type: str) -> FormDataAttachmentType:
    """content_type을 FormDataAttachmentType으로 매핑."""
    ct = content_type.split(";")[0].strip().lower()
    if ct in EVIDENCE_IMAGE_RESTRICT.allowed_types:
        return FormDataAttachmentType.IMAGE
    if ct in EVIDENCE_VIDEO_RESTRICT.allowed_types:
        return FormDataAttachmentType.VIDEO
    if ct in EVIDENCE_VOICE_AUDIO_RESTRICT.allowed_types:
        return FormDataAttachmentType.AUDIO
    if ct in EVIDENCE_DOCUMENT_RESTRICT.allowed_types:
        return FormDataAttachmentType.DOCUMENT
    return FormDataAttachmentType.ETC
