from io import BytesIO

from mutagen import File as MutagenFile


def get_audio_duration(file_bytes: bytes) -> int:
    audio = MutagenFile(fileobj=BytesIO(file_bytes))
    if audio is None:
        raise ValueError("지원하지 않거나 손상된 오디오 형식입니다.")
    return int(round(audio.info.length))
