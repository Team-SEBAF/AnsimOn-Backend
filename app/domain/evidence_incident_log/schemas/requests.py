from app.base.base_request import BaseRequest, create_partial_request
from app.domain.evidence_incident_log.schemas.dtos import EvidenceIncidentLogFormDataDTO


class EvidenceIncidentLogFormDataUploadRequest(BaseRequest, EvidenceIncidentLogFormDataDTO):
    pass


EvidenceIncidentLogFormDataUpdateRequest = create_partial_request(
    EvidenceIncidentLogFormDataDTO, "EvidenceIncidentLogFormDataUpdateRequest"
)
