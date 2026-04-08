import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.settings import settings
from app.domain.evidence.constant import EVIDENCE_IMAGE_RESTRICT

# HEIC/HEIF: pillow-heif 없이 ffmpeg로 디코딩 (Lambda: /opt/bin/ffmpeg + ffmpeg 레이어)
# 썸네일·detail은 항상 JPEG로 저장 (make_image_top_crop)


def _ffmpeg_bin() -> str:
    return "ffmpeg" if settings.env == "local" else "/opt/bin/ffmpeg"


def _heic_to_png_bytes_via_ffmpeg(file_bytes: bytes) -> bytes:
    """HEIC/HEIF를 PNG 바이트로 변환. 정적 ffmpeg는 libheif 빌드가 있어야 함."""
    ffmpeg = _ffmpeg_bin()
    with tempfile.NamedTemporaryFile(suffix=".heic", delete=False) as f:
        f.write(file_bytes)
        path = Path(f.name)
    try:
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-f",
                "image2pipe",
                "-vcodec",
                "png",
                "-",
            ],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0 or not result.stdout:
            raise ValueError(
                "HEIC/HEIF 이미지를 열 수 없습니다. ffmpeg(HEIC 지원 빌드)를 확인해 주세요."
            )
        return result.stdout
    finally:
        path.unlink(missing_ok=True)


def _open_image_for_processing(file_bytes: bytes) -> Image.Image:
    """JPEG/PNG는 PIL, HEIC는 ffmpeg→PNG 후 PIL."""
    try:
        img = Image.open(BytesIO(file_bytes))
        img.load()
        return img
    except (UnidentifiedImageError, OSError):
        png_bytes = _heic_to_png_bytes_via_ffmpeg(file_bytes)
        img = Image.open(BytesIO(png_bytes))
        img.load()
        return img


# PIL Image.format → 허용 MIME (image/heif MIME은 없음)
PIL_FORMAT_TO_IMAGE_MIME: dict[str, str] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "HEIC": "image/heic",
}


def _mime_for_pil_format(fmt: str | None) -> str:
    if not fmt:
        raise ValueError("이미지 포맷을 알 수 없습니다.")
    key = fmt.upper()
    if key == "HEIF":
        key = "HEIC"
    mime = PIL_FORMAT_TO_IMAGE_MIME.get(key)
    if mime is None:
        allowed = ", ".join(sorted(EVIDENCE_IMAGE_RESTRICT.allowed_types))
        raise ValueError(f"지원하지 않는 이미지 포맷입니다: {fmt!r}. 허용 MIME: {allowed}")
    return mime


def extract_image_meta(file_bytes: bytes) -> tuple[int, int, str]:
    """(width, height, content_type). content_type은 증거 이미지 허용 MIME 중 하나."""
    try:
        image = Image.open(BytesIO(file_bytes))
        image.load()
        width, height = image.size
        content_type = _mime_for_pil_format(image.format)
        return width, height, content_type
    except (UnidentifiedImageError, OSError):
        image = _open_image_for_processing(file_bytes)
        width, height = image.size
        # ffmpeg 경로면 원본이 HEIC/HEIF로 간주 (S3 original은 그대로 HEIC)
        return width, height, "image/heic"


def make_image_top_crop(
    file_bytes: bytes,
    size: int,
    quality: int,
) -> tuple[bytes, int, int]:
    """
    - 정사각형(size x size)
    - 가로/세로 중 긴 쪽 기준 리사이즈
    - 상단 기준 크롭
    - 여백/검은 영역 없음
    - 출력은 항상 JPEG
    """
    img = _open_image_for_processing(file_bytes)
    img = img.convert("RGB")

    orig_w, orig_h = img.size

    # scale 결정 (짧은 변이 size 이상이 되도록)
    if orig_w >= orig_h:
        # 가로가 더 긴 경우 → 세로 기준
        scale = size / orig_h
    else:
        # 세로가 더 긴 경우 → 가로 기준
        scale = size / orig_w

    resized_w = int(orig_w * scale)
    resized_h = int(orig_h * scale)

    img = img.resize(
        (resized_w, resized_h),
        Image.Resampling.LANCZOS,
    )

    # 상단 기준 크롭 (가로 중앙, 세로 상단)
    left = max(0, (resized_w - size) // 2)
    upper = 0
    right = left + size
    lower = upper + size

    img = img.crop((left, upper, right, lower))

    buf = BytesIO()
    img.save(
        buf,
        format="JPEG",
        quality=quality,
        optimize=True,
    )
    buf.seek(0)

    return buf.read(), size, size
