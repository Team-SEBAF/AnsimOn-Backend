"""FORM_DATA 사건일지 PDF 생성."""

from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

_FONT_PATH = Path(__file__).parent.parent.parent / "fonts" / "NotoSansKR-Regular.ttf"
_FONT_NAME = "NotoSansKR"

# 한글 폰트 등록 (모듈 로드 시 1회)
if _FONT_PATH.exists():
    pdfmetrics.registerFont(TTFont(_FONT_NAME, str(_FONT_PATH)))


def build_form_data_pdf(
    title: str,
    date_str: str,
    time_str: str,
    location: str,
    description: str,
) -> bytes:
    """제목, 날짜, 시간, 장소, 상황으로 PDF 생성."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 72
    label_font_size = 14
    value_font_size = 10
    line_height = 18
    section_gap = 8
    max_chars = 50  # 한글 기준 줄당 글자 수

    font_name = _FONT_NAME if _FONT_PATH.exists() else "Helvetica"

    def _draw(label: str, value: str) -> None:
        nonlocal y
        # 제목(라벨): 큰 글씨
        c.setFont(font_name, label_font_size)
        c.drawString(72, y, label)
        y -= line_height

        # 내용: 작은 글씨, 여러 줄
        val = (value or "-").replace("\r\n", "\n").replace("\r", "\n")
        c.setFont(font_name, value_font_size)
        for line in val.split("\n"):
            for j in range(0, len(line), max_chars):
                chunk = line[j : j + max_chars]
                c.drawString(72, y, chunk)
                y -= line_height

        y -= section_gap

    _draw("제목", title)
    _draw("날짜", date_str)
    _draw("시간", time_str)
    _draw("장소", location)
    _draw("상황", description)

    c.save()
    return buffer.getvalue()
