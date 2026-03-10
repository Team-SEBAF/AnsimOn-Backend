import re
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

from app.core.settings import settings


def get_video_duration(file_bytes: bytes) -> int:
    ffmpeg = "ffmpeg" if settings.env == "local" else "/opt/bin/ffmpeg"
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(file_bytes)
        path = Path(f.name)

    try:
        result = subprocess.run(
            [
                ffmpeg,
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
