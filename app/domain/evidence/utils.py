import mimetypes
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from typing import Callable, TypedDict, TypeVar
from uuid import UUID

from fastapi import UploadFile
from mutagen import File as MutagenFile
from PIL import Image, ImageOps

from app.base.base_error import CodeException
from app.core.aws import head_s3_object
from app.core.settings import settings
from app.domain.complaint import Complaint
from app.domain.evidence.constant import EvidenceTypeRestrict
from app.domain.evidence.errors.evidence_max_count_exceeded_error import (
    EvidenceMaxCountExceededErrorCode,
)
from app.domain.evidence.errors.s3_not_uploaded_yet_error import (
    S3NotUploadedYetErrorCode,
)

T = TypeVar("T")


def check_register_max_count(
    total_count: int,
    request_count: int,
    restrict: EvidenceTypeRestrict,
    type_name: str,
) -> None:
    """total_count + request_count가 restrict.max_count 초과 시 CodeException raise."""
    if total_count + request_count > restrict.max_count:
        raise CodeException(
            code=EvidenceMaxCountExceededErrorCode.EVIDENCE_MAX_COUNT_EXCEEDED,
            message=f"{type_name} 타입 증거의 최대 개수({restrict.max_count}개)를 초과합니다. (현재 {total_count}개 + 요청 {request_count}개)",
            status_code=400,
        )


def validate_s3_uploads_before_register(
    complaint: Complaint,
    items: list[T],
    path_segment: str,
    get_evidence_id: Callable[[T], UUID],
) -> None:
    """S3에 업로드되지 않은 항목이 있으면 CodeException raise."""

    def _check(item: T) -> UUID | None:
        s3_key = (
            f"{complaint.user_sub}/complaints/"
            f"{complaint.complaint_id}/evidences/{path_segment}/{get_evidence_id(item)}/original"
        )
        return (
            get_evidence_id(item)
            if head_s3_object(settings.S3_BUCKET_NAME, s3_key) is None
            else None
        )

    with ThreadPoolExecutor(max_workers=max(1, min(len(items), 5))) as executor:
        failed_ids = [eid for eid in executor.map(_check, items) if eid is not None]

    if failed_ids:
        raise CodeException(
            code=S3NotUploadedYetErrorCode.S3_NOT_UPLOADED_YET,
            message="S3에 파일이 업로드되지 않은 증거가 있습니다. 먼저 presigned URL로 업로드해 주세요.",
            status_code=400,
            detail={"failed_evidence_ids": [str(eid) for eid in failed_ids]},
        )


def fetch_s3_metadata_for_register(
    complaint: Complaint,
    items: list[T],
    path_segment: str,
    get_evidence_id: Callable[[T], UUID],
    build_extra: Callable[[T, str, str, int], dict] | None = None,
) -> list[dict]:
    """
    S3 head_object로 content_type, size_bytes 조회.
    없으면 S3_NOT_UPLOADED_YET raise. 반환: list of {evidence_id, s3_key, content_type, size_bytes, ...extra}
    """

    def _fetch(item: T) -> tuple[dict | None, UUID | None]:
        eid = get_evidence_id(item)
        s3_key = (
            f"{complaint.user_sub}/complaints/"
            f"{complaint.complaint_id}/evidences/{path_segment}/{eid}/original"
        )
        meta = head_s3_object(settings.S3_BUCKET_NAME, s3_key)
        if meta is None:
            return None, eid
        content_type = meta.get("ContentType") or "application/octet-stream"
        size_bytes = meta.get("ContentLength") or 0
        row: dict = {
            "evidence_id": eid,
            "s3_key": s3_key,
            "content_type": content_type,
            "size_bytes": size_bytes,
        }
        if build_extra:
            row.update(build_extra(item, s3_key, content_type, size_bytes))
        return row, None

    with ThreadPoolExecutor(max_workers=max(1, min(len(items), 5))) as executor:
        results = list(executor.map(_fetch, items))

    failed_ids = [eid for _, eid in results if eid is not None]
    if failed_ids:
        raise CodeException(
            code=S3NotUploadedYetErrorCode.S3_NOT_UPLOADED_YET,
            message="S3에 파일이 업로드되지 않은 증거가 있습니다. 먼저 presigned URL로 업로드해 주세요.",
            status_code=400,
            detail={"failed_evidence_ids": [str(eid) for eid in failed_ids]},
        )

    return [r for r, _ in results]


def get_audio_duration(file_bytes: bytes) -> int:
    audio = MutagenFile(fileobj=BytesIO(file_bytes))
    if audio is None:
        raise ValueError("지원하지 않거나 손상된 오디오 형식입니다.")
    return int(round(audio.info.length))


def get_audio_content_type(file_bytes: bytes) -> str:
    """mutagen으로 오디오 content_type 추출. 실패 시 application/octet-stream."""
    audio = MutagenFile(fileobj=BytesIO(file_bytes))
    if audio is None:
        return "application/octet-stream"
    # mutagen 타입별 MIME 매핑
    type_name = type(audio).__name__
    mime_map = {
        "MP3": "audio/mpeg",
        "ID3": "audio/mpeg",
        "MP4": "audio/mp4",
        "M4A": "audio/mp4",
        "OggVorbis": "audio/ogg",
        "OggOpus": "audio/opus",
        "FLAC": "audio/flac",
        "WAVE": "audio/wav",
    }
    return mime_map.get(type_name, "application/octet-stream")


def get_content_type_from_filename(filename: str) -> str:
    """파일 확장자로 content_type 추정."""
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def get_video_duration(file_bytes: bytes) -> int:
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(file_bytes)
        path = Path(f.name)

    try:
        result = subprocess.run(
            [
                "/opt/bin/ffmpeg",  # Lambda용 절대경로 추천
                "-i",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # ffmpeg는 -i만 쓰면 항상 returncode != 0 이 나옴
        output = result.stderr

        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", output)
        if not match:
            raise ValueError("영상 길이를 읽을 수 없습니다.")

        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))

        total_seconds = hours * 3600 + minutes * 60 + seconds
        return int(round(total_seconds))

    except FileNotFoundError:
        raise ValueError("영상 길이 계산에 필요한 ffmpeg가 없습니다.") from None
    finally:
        path.unlink(missing_ok=True)


def get_video_image_at_0(
    file_bytes: bytes,
    size: int,
    quality: int,
) -> tuple[bytes, int, int]:
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f_in:
        f_in.write(file_bytes)
        path_in = Path(f_in.name)
    path_out = path_in.with_suffix(".jpg")
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(path_in),
                "-ss",
                "0",
                "-vframes",
                "1",
                "-f",
                "image2",
                str(path_out),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0 or not path_out.exists():
            raise ValueError(
                "영상 썸네일을 추출할 수 없습니다. 지원하지 않거나 손상된 형식일 수 있습니다."
            )
        frame_bytes = path_out.read_bytes()
    except FileNotFoundError:
        raise ValueError(
            "썸네일 추출에 필요한 ffmpeg가 없습니다. ffmpeg를 설치해 주세요. (예: brew install ffmpeg)"
        ) from None
    finally:
        path_in.unlink(missing_ok=True)
        path_out.unlink(missing_ok=True)

    img = Image.open(BytesIO(frame_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    orig_w, orig_h = img.size

    if orig_w >= orig_h:
        scale = size / orig_h
    else:
        scale = size / orig_w

    resized_w = int(orig_w * scale)
    resized_h = int(orig_h * scale)
    img = img.resize((resized_w, resized_h), Image.Resampling.LANCZOS)

    left = max(0, (resized_w - size) // 2)
    upper = 0
    right = left + size
    lower = upper + size
    img = img.crop((left, upper, right, lower))

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    return buf.read(), size, size


class FilterEvidenceFilesResult(TypedDict):
    valid_files: list
    type_invalid_filenames: list[str]
    size_invalid_filenames: list[str]
    duration_invalid_filenames: list[str] | None


def filter_evidence_files(
    files: list[UploadFile],
    restrict: EvidenceTypeRestrict,
    need_audio_duration_check: bool = False,
    need_video_duration_check: bool = False,
) -> FilterEvidenceFilesResult:
    valid_files: list[UploadFile] | list[tuple[UploadFile, bytes, int]] = []
    type_invalid_filenames: list[str] = []
    size_invalid_filenames: list[str] = []
    duration_invalid_filenames: list[str] | None = (
        [] if (need_audio_duration_check or need_video_duration_check) else None
    )

    for file in files:
        if file.content_type not in restrict.allowed_types:
            print(f"type_invalid_filenames: {file.filename} ({file.content_type})")
            type_invalid_filenames.append(file.filename)
            continue

        if file.size > restrict.max_size_bytes:
            size_invalid_filenames.append(file.filename)
            continue

        if need_audio_duration_check:
            file_bytes = file.file.read()
            duration_seconds = get_audio_duration(file_bytes)
            if duration_seconds > restrict.max_duration_seconds:
                duration_invalid_filenames.append(file.filename)
                continue
            valid_files.append((file, file_bytes, duration_seconds))

        elif need_video_duration_check:
            file_bytes = file.file.read()
            duration_seconds = get_video_duration(file_bytes)
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
