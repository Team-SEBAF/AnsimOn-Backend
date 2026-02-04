from uuid import UUID

from pydantic import BaseModel


class EvidenceMessageResponse(BaseModel):
    message_id: UUID
    filename: str
    width: int | None
    height: int | None
    size_bytes: int


class EvidenceMessageUploadResponse(BaseModel):
    messages: list[EvidenceMessageResponse]


class EvidenceMessageOriginalImageResponse(BaseModel):
    message_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    width: int | None
    height: int | None
    url: str
