from app.domain.evidence.errors.get_evidence_error import GET_EVIDENCE_ERRORS_RESPONSES

from . import incident_log_type_mismatch_error

INCIDENT_LOG_ACCESS_AND_TYPE_CHECK_RESPONSES = {
    **GET_EVIDENCE_ERRORS_RESPONSES,
    **incident_log_type_mismatch_error.INCIDENT_LOG_TYPE_MISMATCH_ERRORS_RESPONSES,
}

__all__ = [
    "INCIDENT_LOG_ACCESS_AND_TYPE_CHECK_RESPONSES",
    "incident_log_type_mismatch_error",
]
