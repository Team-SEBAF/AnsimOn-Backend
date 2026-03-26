from io import BytesIO

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from app.domain.evidence.constant import EVIDENCE_IMAGE_RESTRICT

# HEIC 디코딩용 (패키지 이름만 pillow-heif; 클라이언트·허용 MIME은 image/heic만)
register_heif_opener()

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
    # HEIC(.heic)만 업로드 허용. libheif+PIL은 같은 파일도 format 문자열을 "HEIF"로 줄 수 있음(표준 MIME image/heif와 무관).
    if key == "HEIF":
        key = "HEIC"
    mime = PIL_FORMAT_TO_IMAGE_MIME.get(key)
    if mime is None:
        allowed = ", ".join(sorted(EVIDENCE_IMAGE_RESTRICT.allowed_types))
        raise ValueError(f"지원하지 않는 이미지 포맷입니다: {fmt!r}. 허용 MIME: {allowed}")
    return mime


def extract_image_meta(file_bytes: bytes) -> tuple[int, int, str]:
    """(width, height, content_type) 반환. content_type은 증거 이미지 허용 MIME 중 하나."""
    image = Image.open(BytesIO(file_bytes))
    image = ImageOps.exif_transpose(image)
    width, height = image.size
    content_type = _mime_for_pil_format(image.format)
    return width, height, content_type


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
    """
    img = Image.open(BytesIO(file_bytes))
    img = ImageOps.exif_transpose(img)
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
