import mimetypes
import subprocess
import tempfile
from pathlib import Path

from app.domain.evidence_message.utils import _ffmpeg_bin

_AUDIO_TO_MP3_TYPES = frozenset(
    {
        "audio/wav",
        "audio/x-wav",
        "audio/mp4",
        "audio/x-m4a",
        "audio/mp4a-latm",
    }
)


def _normalized_content_type(content_type: str | None) -> str | None:
    if not content_type:
        return None
    return content_type.split(";")[0].strip().lower()


def _ext_from_content_type(content_type: str | None, default: str = ".bin") -> str:
    """Content-Type에서 확장자 추출. audio/mp4a-latm은 mimetypes 미지원이라 fallback."""
    ct = _normalized_content_type(content_type)
    if not ct:
        return default
    if ct == "audio/mp4a-latm":
        return ".m4a"
    return mimetypes.guess_extension(ct) or default


def _audio_input_suffix(content_type: str) -> str:
    """ffmpeg 임시 입력 파일 확장자. _to_mp3_bytes에서만 사용."""
    if content_type in ("audio/wav", "audio/x-wav"):
        return ".wav"
    if content_type in ("audio/mp4", "audio/x-m4a", "audio/mp4a-latm"):
        return ".m4a"
    return ".bin"


def _ffmpeg_transcode(
    file_bytes: bytes,
    *,
    input_suffix: str,
    output_suffix: str,
    extra_args: list[str],
    timeout: int,
    error_message: str,
) -> bytes:
    ffmpeg = _ffmpeg_bin()
    with tempfile.NamedTemporaryFile(suffix=input_suffix, delete=False) as f_in:
        f_in.write(file_bytes)
        path_in = Path(f_in.name)
    path_out = path_in.with_suffix(output_suffix)
    try:
        result = subprocess.run(
            [ffmpeg, "-y", "-i", str(path_in), *extra_args, str(path_out)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0 or not path_out.exists():
            raise ValueError(error_message)
        return path_out.read_bytes()
    except FileNotFoundError:
        raise ValueError(
            "미디어 변환에 필요한 ffmpeg가 없습니다. ffmpeg를 설치해 주세요. (예: brew install ffmpeg)"
        ) from None
    finally:
        path_in.unlink(missing_ok=True)
        path_out.unlink(missing_ok=True)


def _to_mp3_bytes(file_bytes: bytes, content_type: str) -> bytes:
    return _ffmpeg_transcode(
        file_bytes,
        input_suffix=_audio_input_suffix(content_type),
        output_suffix=".mp3",
        extra_args=["-vn", "-acodec", "libmp3lame", "-q:a", "2"],
        timeout=180,
        error_message="오디오를 MP3로 변환할 수 없습니다.",
    )


def _to_mp4_bytes(file_bytes: bytes) -> bytes:
    return _ffmpeg_transcode(
        file_bytes,
        input_suffix=".mov",
        output_suffix=".mp4",
        extra_args=["-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart"],
        timeout=600,
        error_message="영상을 MP4로 변환할 수 없습니다.",
    )


def prepare_evidence_bytes_for_zip(data: bytes, content_type: str | None) -> tuple[bytes, str]:
    """ZIP 다운로드용: OS 호환을 위해 wav/m4a→mp3, quicktime→mp4로 변환."""
    ct = _normalized_content_type(content_type)
    if ct in _AUDIO_TO_MP3_TYPES:
        return _to_mp3_bytes(data, ct), ".mp3"
    if ct == "video/quicktime":
        return _to_mp4_bytes(data), ".mp4"
    return data, _ext_from_content_type(content_type)
