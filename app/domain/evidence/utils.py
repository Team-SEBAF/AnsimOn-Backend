from typing import TypedDict

from fastapi import UploadFile

from app.domain.evidence.constant import EvidenceTypeRestrict


class FilterEvidenceFilesResult(TypedDict):
    valid_files: list
    type_invalid_filenames: list[str]
    size_invalid_filenames: list[str]
    length_invalid_filenames: list[str] | None
    duration_invalid_filenames: list[str] | None


def filter_evidence_files(
    files: list[UploadFile],
    restrict: EvidenceTypeRestrict,
) -> FilterEvidenceFilesResult:
    valid_files: list[UploadFile] = []
    type_invalid_filenames: list[str] = []
    size_invalid_filenames: list[str] = []
    length_invalid_filenames: list[str] | None = [] if restrict.max_length_seconds else None
    duration_invalid_filenames: list[str] | None = [] if restrict.max_duration_seconds else None

    for file in files:
        if file.content_type not in restrict.allowed_types:
            type_invalid_filenames.append(file.filename)
            continue

        if file.size > restrict.max_size_bytes:
            size_invalid_filenames.append(file.filename)
            continue

        if length_invalid_filenames and file.size > restrict.max_length_seconds:
            length_invalid_filenames.append(file.filename)
            continue

        if duration_invalid_filenames and file.size > restrict.max_duration_seconds:
            duration_invalid_filenames.append(file.filename)
            continue

        valid_files.append(file)

    return FilterEvidenceFilesResult(
        valid_files=valid_files,
        type_invalid_filenames=type_invalid_filenames,
        size_invalid_filenames=size_invalid_filenames,
        length_invalid_filenames=length_invalid_filenames,
        duration_invalid_filenames=duration_invalid_filenames,
    )
