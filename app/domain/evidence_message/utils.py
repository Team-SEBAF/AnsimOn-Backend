from io import BytesIO

from fastapi import UploadFile
from PIL import Image, ImageOps

from .constant import ALLOWED_IMAGE_TYPES


def filter_image_files(
    files: list[UploadFile],
) -> tuple[list[UploadFile], list[str]]:
    valid_files: list[UploadFile] = []
    invalid_filenames: list[str] = []

    for file in files:
        if file.content_type in ALLOWED_IMAGE_TYPES:
            valid_files.append(file)
        else:
            invalid_filenames.append(file.filename)

    return valid_files, invalid_filenames


def extract_image_meta(file_bytes: bytes) -> tuple[int, int]:
    image = Image.open(BytesIO(file_bytes))
    image = ImageOps.exif_transpose(image)
    width, height = image.size
    return width, height


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
