from reportlab.lib.pagesizes import A4

PAGE_WIDTH, PAGE_HEIGHT = A4

# -------------------------
# Page padding
# -------------------------

PAGE_PADDING_TOP = 24
PAGE_PADDING_RIGHT = 24
PAGE_PADDING_BOTTOM = 36
PAGE_PADDING_LEFT = 24

CONTENT_WIDTH = PAGE_WIDTH - PAGE_PADDING_LEFT - PAGE_PADDING_RIGHT

# -------------------------
# Header
# -------------------------

HEADER_WIDTH = 547
HEADER_HEIGHT = 50

HEADER_LEFT_WIDTH = 400
HEADER_RIGHT_WIDTH = 147

HEADER_TOP_Y = PAGE_HEIGHT - PAGE_PADDING_TOP
HEADER_BOTTOM_Y = HEADER_TOP_Y - HEADER_HEIGHT

# -------------------------
# Footer
# -------------------------

FOOTER_HEIGHT = 10

FOOTER_BOTTOM_Y = PAGE_PADDING_BOTTOM
FOOTER_TOP_Y = FOOTER_BOTTOM_Y + FOOTER_HEIGHT

# -------------------------
# Content area
# (timeline이 들어갈 영역)
# -------------------------

CONTENT_TOP_Y = HEADER_BOTTOM_Y - 12
CONTENT_BOTTOM_Y = FOOTER_TOP_Y + 12

CONTENT_HEIGHT = CONTENT_TOP_Y - CONTENT_BOTTOM_Y
