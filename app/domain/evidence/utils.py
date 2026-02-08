from io import BytesIO
from typing import TypedDict

from fastapi import UploadFile
from mutagen import File as MutagenFile

from app.domain.evidence.constant import EvidenceTypeRestrict


def get_audio_duration(file_bytes: bytes) -> int:
    audio = MutagenFile(fileobj=BytesIO(file_bytes))
    if audio is None:
        raise ValueError("지원하지 않거나 손상된 오디오 형식입니다.")
    return int(round(audio.info.length))


class FilterEvidenceFilesResult(TypedDict):
    valid_files: list
    type_invalid_filenames: list[str]
    size_invalid_filenames: list[str]
    duration_invalid_filenames: list[str] | None


def filter_evidence_files(
    files: list[UploadFile],
    restrict: EvidenceTypeRestrict,
    need_duration_check: bool = False,
) -> FilterEvidenceFilesResult:
    valid_files: list[UploadFile] | list[tuple[UploadFile, bytes, int]] = []
    type_invalid_filenames: list[str] = []
    size_invalid_filenames: list[str] = []
    duration_invalid_filenames: list[str] | None = [] if need_duration_check else None

    for file in files:
        if file.content_type not in restrict.allowed_types:
            type_invalid_filenames.append(file.filename)
            continue

        if file.size > restrict.max_size_bytes:
            size_invalid_filenames.append(file.filename)
            continue

        if need_duration_check:
            file_bytes = file.file.read()

            duration_seconds = get_audio_duration(file_bytes)
            if duration_seconds > restrict.max_duration_seconds:
                duration_invalid_filenames.append(file.filename)
                continue

            valid_files.append((file, file_bytes, duration_seconds))
        else:
            valid_files.append(file)

    return FilterEvidenceFilesResult(
        valid_files=valid_files,
        type_invalid_filenames=type_invalid_filenames,
        size_invalid_filenames=size_invalid_filenames,
        duration_invalid_filenames=duration_invalid_filenames,
    )
