from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = Path(__file__).parent / "static" / "fonts"

FONT_FILES = {
    "regular": "NotoSansKR-Regular.ttf",
    "medium": "NotoSansKR-Medium.ttf",
    "semibold": "NotoSansKR-SemiBold.ttf",
}

FONT_NAMES = {}

for weight, file in FONT_FILES.items():
    path = FONT_DIR / file
    font_name = f"NotoSansKR-{weight}"

    if path.exists():
        pdfmetrics.registerFont(TTFont(font_name, str(path)))
        FONT_NAMES[weight] = font_name


def get_font(weight: str = "regular") -> str:
    """
    weight:
        regular
        medium
        semibold
    """
    return FONT_NAMES.get(weight, "Helvetica")
