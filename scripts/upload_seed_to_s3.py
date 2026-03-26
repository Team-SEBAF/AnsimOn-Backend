#!/usr/bin/env python3
"""
seed_timeline_evidence.sql 기준으로 dummy 폴더 파일을 S3에 일괄 업로드.
_s3_keys_from_seed 순서대로 dummy 파일 사용. pdf는 pdf_ex.pdf.
이미지/영상은 evidence 서비스와 동일하게 detail 추출 후 {base}/detail 업로드.
"""

import mimetypes
import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.aws import upload_fileobj
from app.core.settings import settings
from app.domain.evidence_message.utils import make_image_top_crop

# evidence 서비스와 동일: 이미지(jpeg,png,heic) / 영상(mp4,quicktime)
_IMAGE_TYPES = {"image/jpeg", "image/png", "image/heic"}
_VIDEO_TYPES = {"video/mp4", "video/quicktime"}


def _make_image_top_crop(file_bytes: bytes, size: int, quality: int) -> bytes:
    """이미지 → 정사각형 썸네일 (evidence_message.utils.make_image_top_crop과 동일)."""
    out, _, _ = make_image_top_crop(file_bytes=file_bytes, size=size, quality=quality)
    return out


def _get_video_image_at_0(file_bytes: bytes, size: int, quality: int) -> bytes:
    """영상 0초 프레임 → 정사각형 썸네일 (evidence_victim.utils와 동일)."""
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
            raise SystemExit("영상 썸네일 추출 실패. ffmpeg 설치 확인: brew install ffmpeg")
        frame_bytes = path_out.read_bytes()
    finally:
        path_in.unlink(missing_ok=True)
        path_out.unlink(missing_ok=True)
    img = Image.open(BytesIO(frame_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    orig_w, orig_h = img.size
    scale = size / orig_h if orig_w >= orig_h else size / orig_w
    resized_w, resized_h = int(orig_w * scale), int(orig_h * scale)
    img = img.resize((resized_w, resized_h), Image.Resampling.LANCZOS)
    left = max(0, (resized_w - size) // 2)
    img = img.crop((left, 0, left + size, size))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    buf.seek(0)
    return buf.read()


# seed SQL과 동일한 상수
USER_SUB = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
COMPLAINT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
BASE = f"{USER_SUB}/complaints/{COMPLAINT_ID}/evidences"

# _s3_keys_from_seed 순서와 동일한 dummy 파일 목록. pdf는 pdf_ex.pdf
DUMMY_PATHS_ORDERED: list[str] = [
    "dummy/MESSAGE_1.jpg",
    "dummy/MESSAGE_2.jpg",
    "dummy/MESSAGE_3.png",
    "dummy/MESSAGE_4.jpg",
    "dummy/MESSAGE_5.jpg",
    "dummy/MESSAGE_6.jpg",
    "dummy/MESSAGE_7.png",
    "dummy/MESSAGE_8.jpg",
    "dummy/MESSAGE_9.jpg",
    "dummy/VICTIM_IMAGE_1.png",
    "dummy/VICTIM_VIDEO.mov",
    "dummy/VICTIM_IMAGE_2.png",
    "dummy/VOICE_IMAGE.png",
    "dummy/VOICE_AUDIO_1.m4a",
    "dummy/VOICE_AUDIO_2.m4a",
    "dummy/pdf_ex.pdf",
    "dummy/pdf_ex.pdf",
    "dummy/pdf_ex.pdf",
    "dummy/ATTACHMENT.png",
]


def _content_type_from_path(path: Path) -> str:
    """파일 확장자에서 content_type 추출."""
    ct, _ = mimetypes.guess_type(str(path), strict=False)
    return ct or "application/octet-stream"


def _needs_detail(s3_key: str, content_type: str) -> bool:
    """이미지/영상이면 detail 추출 (evidence 서비스와 동일). attachment는 original만."""
    if "/incident-logs/attachments/" in s3_key:
        return False
    return content_type in _IMAGE_TYPES or content_type in _VIDEO_TYPES


def _generate_detail(file_bytes: bytes, content_type: str) -> bytes:
    """이미지: make_image_top_crop, 영상: get_video_image_at_0 (evidence 서비스 detail와 동일, size=400)."""
    if content_type in _VIDEO_TYPES:
        return _get_video_image_at_0(file_bytes, size=400, quality=75)
    return _make_image_top_crop(file_bytes, size=400, quality=75)


def _s3_keys_from_seed() -> list[tuple[str, str]]:
    """seed_timeline_evidence.sql + DUMMY_PATHS_ORDERED와 매칭되는 (s3_key, content_type) 목록."""
    return [
        # evidence_messages (9개) - MESSAGE_1.jpg~MESSAGE_9.jpg/.png
        (f"{BASE}/messages/08e070bb-fb4e-4176-a450-375f947d1ef7/original", "image/jpeg"),
        (f"{BASE}/messages/db9d9261-b523-4be9-9e9e-52ad6e75150e/original", "image/jpeg"),
        (f"{BASE}/messages/78be5c14-bfae-40a0-8bae-9159105c1748/original", "image/png"),
        (f"{BASE}/messages/702eddc4-1eaf-4380-86dc-16b9bed5cf62/original", "image/jpeg"),
        (f"{BASE}/messages/83f41aee-f3a7-40d0-8740-080b7b0de4d5/original", "image/jpeg"),
        (f"{BASE}/messages/7c8d9e0f-1a2b-4c3d-9e5f-6a7b8c9d0e1f/original", "image/jpeg"),
        (f"{BASE}/messages/8d9e0f1a-2b3c-4d4e-0f6a-7b8c9d0e1f2a/original", "image/png"),
        (f"{BASE}/messages/9e0f1a2b-3c4d-4e5f-1a7b-8c9d0e1f2a3b/original", "image/jpeg"),
        (f"{BASE}/messages/0f1a2b3c-4d5e-4f6a-2b8c-9d0e1f2a3b4c/original", "image/jpeg"),
        # evidence_victims (3개) - VICTIM_IMAGE_1.png, VICTIM_VIDEO.mov, VICTIM_IMAGE_2.png
        (f"{BASE}/victims/6de0bca2-6b96-4489-ab10-8e13033d40b0/original", "image/png"),
        (f"{BASE}/victims/6a259984-0ba4-4d5e-b27b-55fb694eecbf/original", "video/quicktime"),
        (f"{BASE}/victims/f15547c2-8278-4aa1-8422-add6ae43d368/original", "image/png"),
        # evidence_voices (3개)
        (f"{BASE}/voices/457329d6-d9e9-418a-9464-65f4fc7da8f8/original", "image/png"),
        (f"{BASE}/voices/a1b29641-c680-43a5-a713-fa4842469960/original", "audio/mp4"),
        (f"{BASE}/voices/672626d0-21ac-4f95-8711-6b67105a06f2/original", "audio/mp4"),
        # evidence_report_records (2개)
        (f"{BASE}/report-records/f8166b42-1ffb-4c1f-a48d-8d2234476652/original", "application/pdf"),
        (f"{BASE}/report-records/3a4b5c6d-7e8f-4a9b-0c1d-2e3f4a5b6c7d/original", "application/pdf"),
        # evidence_incident_log_files (FILE 1개)
        (f"{BASE}/incident-logs/4b5c6d7e-8f9a-4b0c-1d2e-3f4a5b6c7d8e/original", "application/pdf"),
        # incident_log_form_data_attachments (1개)
        (
            f"{BASE}/incident-logs/attachments/2c504997-7042-4ac6-a8fe-cf42c31fbea4/9d4e5f6a-7b8c-4d9e-af01-23456789abcd/original",
            "image/png",
        ),
    ]


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    bucket = settings.S3_BUCKET_NAME
    if not bucket:
        raise SystemExit("S3_BUCKET_NAME 환경변수가 필요합니다.")

    items = _s3_keys_from_seed()
    if len(items) != len(DUMMY_PATHS_ORDERED):
        raise SystemExit(
            f"_s3_keys_from_seed({len(items)})와 DUMMY_PATHS_ORDERED({len(DUMMY_PATHS_ORDERED)}) 개수 불일치"
        )

    for (s3_key, _), dummy_path in zip(items, DUMMY_PATHS_ORDERED):
        local_path = root / dummy_path
        if not local_path.exists():
            raise SystemExit(f"파일 없음: {local_path}")

        content_type = _content_type_from_path(local_path)
        file_bytes = local_path.read_bytes()
        upload_fileobj(BytesIO(file_bytes), bucket, s3_key, content_type)
        print(f"OK {s3_key} <- {dummy_path}")

        if _needs_detail(s3_key, content_type):
            base_key = s3_key.rsplit("/", 1)[0]
            detail_key = f"{base_key}/detail"
            detail_bytes = _generate_detail(file_bytes, content_type)
            upload_fileobj(
                fileobj=BytesIO(detail_bytes),
                bucket=bucket,
                key=detail_key,
                content_type="image/jpeg",
            )
            print(f"OK {detail_key} <- detail 추출")

    print(f"\n총 {len(items)}개 original + detail 업로드 완료.")


if __name__ == "__main__":
    main()
