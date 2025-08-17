# Configuration file for Whisky Label Generator

# Label dimensions (in millimeters)
DEFAULT_LABEL_WIDTH_MM = 35
DEFAULT_LABEL_HEIGHT_MM = 37

# QR Code settings
QR_CODE_SIZE_RATIO = 5  # QR code is 1/5 of the smaller label dimension

# Font settings
BASE_FONT_SIZE_RATIO = 20  # Base font size is 1/20 of smaller label dimension
LARGE_FONT_MULTIPLIER = 1.5
MEDIUM_FONT_MULTIPLIER = 1.2
SMALL_FONT_MULTIPLIER = 0.8

# Margins and spacing
MARGIN_RATIO = 20  # Margin is 1/20 of label dimension
LINE_HEIGHT_RATIO = 15  # Line height is 1/15 of label height

# Print quality settings
DPI = 300  # Dots per inch for print quality
PIXELS_PER_MM = DPI / 25.4  # Convert mm to pixels

# Colors
BACKGROUND_COLOR = '#F5F5DC'  # Cream background
TEXT_COLOR_PRIMARY = '#2F2F2F'  # Dark gray for main text
TEXT_COLOR_SECONDARY = '#4A4A4A'  # Medium gray for secondary text
TEXT_COLOR_TERTIARY = '#666666'  # Light gray for tertiary text

# Whiskybase settings
WHISKYBASE_BASE_URL = "https://www.whiskybase.com"
TIMEOUT_SECONDS = 20

# Label text
LABEL_TITLE = "WHISKY LABEL"
SCAN_TEXT = "Scan for details"
