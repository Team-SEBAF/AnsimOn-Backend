from pydantic import Field

from app.base.base_request import BaseRequest
from app.domain.complaint.models.complaint_model import ComplaintStep


class UpdateComplaintRequest(BaseRequest):
    name: str = Field(..., description="고소장 제목", examples=["고소장 제목"])
    step: ComplaintStep = Field(..., description="고소장 단계", examples=[ComplaintStep.DOCUMENT])
