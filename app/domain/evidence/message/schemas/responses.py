from uuid import UUID

from pydantic import BaseModel


class EvidenceMessageResponse(BaseModel):
    id: UUID
    filename: str
    width: int | None
    height: int | None
    size_bytes: int


class EvidenceMessageUploadResponse(BaseModel):
    messages: list[EvidenceMessageResponse]
