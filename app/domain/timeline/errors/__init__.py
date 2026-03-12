from .get_timeline_error import (
    GET_TIMELINE_ERRORS_RESPONSES,
    GetTimelineErrorCode,
)
from .timeline_manual_evidence_not_allowed_error import (
    TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED_ERRORS_RESPONSES,
    TimelineManualEvidenceNotAllowedErrorCode,
)

MANUAL_TIMELINE_EVIDENCE_RESPONSES = {
    **GET_TIMELINE_ERRORS_RESPONSES,
    **TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED_ERRORS_RESPONSES,
}

__all__ = [
    "GetTimelineErrorCode",
    "GET_TIMELINE_ERRORS_RESPONSES",
    "MANUAL_TIMELINE_EVIDENCE_RESPONSES",
    "TimelineManualEvidenceNotAllowedErrorCode",
    "TIMELINE_MANUAL_EVIDENCE_NOT_ALLOWED_ERRORS_RESPONSES",
]
