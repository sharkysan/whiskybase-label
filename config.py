# Configuration file for Whisky Label Generator

# Label dimensions (width, height) in pixels
LABEL_SIZE = (400, 600)

# QR code size in pixels
QR_CODE_SIZE = 150

# Font sizes
FONT_LARGE = 24
FONT_MEDIUM = 18
FONT_SMALL = 14

# Colors (RGB tuples)
COLORS = {
    'background': (255, 255, 255),  # White
    'text': (0, 0, 0),              # Black
    'border': (0, 0, 0),            # Black
    'error': (255, 0, 0),           # Red
    'accent': (102, 126, 234)       # Blue
}

# Whiskybase settings
WHISKYBASE_BASE_URL = "https://www.whiskybase.com"
REQUEST_TIMEOUT = 15

# User agent for web scraping
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Label text customization
LABEL_TEXTS = {
    'title': 'WHISKY LABEL',
    'scan_instruction': 'Scan for details',
    'name_prefix': 'Name: ',
    'distillery_prefix': 'Distillery: ',
    'region_prefix': 'Region: ',
    'age_prefix': 'Age: ',
    'id_prefix': 'ID: ',
    'note_prefix': 'Note: '
}

# File output settings
DEFAULT_OUTPUT_FORMAT = 'PNG'
DEFAULT_FILENAME_PATTERN = 'whisky_{id}_label.png'
