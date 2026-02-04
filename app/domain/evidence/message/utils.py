from io import BytesIO

from PIL import Image, ImageOps


def extract_image_meta(file_bytes: bytes) -> tuple[int, int]:
    image = Image.open(BytesIO(file_bytes))
    image = ImageOps.exif_transpose(image)
    width, height = image.size
    return width, height
