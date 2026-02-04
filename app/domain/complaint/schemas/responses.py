from app.base.base_response import BaseResponse
from app.domain.complaint.schemas.dtos import ComplaintDTO


class ComplaintResponse(BaseResponse, ComplaintDTO):
    pass
