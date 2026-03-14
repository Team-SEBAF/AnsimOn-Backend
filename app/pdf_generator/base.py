"""PDF 공통 설정: 폰트 등록 등."""

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONT_PATH = Path(__file__).parent.parent / "fonts" / "NotoSansKR-Regular.ttf"
FONT_NAME = "NotoSansKR"

# 한글 폰트 등록 (모듈 로드 시 1회)
if _FONT_PATH.exists():
    pdfmetrics.registerFont(TTFont(FONT_NAME, str(_FONT_PATH)))


def get_pdf_font_name() -> str:
    """PDF에 사용할 폰트 이름. NotoSansKR 없으면 Helvetica."""
    return FONT_NAME if _FONT_PATH.exists() else "Helvetica"
