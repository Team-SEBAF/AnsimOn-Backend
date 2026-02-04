from io import BytesIO

from PIL import Image, ImageOps


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
    상단 기준 정사각형 이미지 생성

    - size x size
    - 비율 무시
    - 상단 기준 크롭
    - JPEG
    """
    img = Image.open(BytesIO(file_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")

    orig_w, orig_h = img.size

    # 가로 기준 리사이즈
    scale = size / orig_w
    resized_h = int(orig_h * scale)

    img = img.resize(
        (size, resized_h),
        Image.Resampling.LANCZOS,
    )

    # 상단 기준 크롭
    img = img.crop((0, 0, size, size))

    buf = BytesIO()
    img.save(
        buf,
        format="JPEG",
        quality=quality,
        optimize=True,
    )
    buf.seek(0)

    return buf.read(), size, size
