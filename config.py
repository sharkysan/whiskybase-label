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

# QL-820NWB Printer Settings
QL820NWB_SETTINGS = {
    'dpi': 300,  # Optimal DPI for QL-820NWB
    'background_color': '#FFFFFF',  # Pure white for thermal printing
    'text_color': '#000000',  # Pure black for maximum contrast
    'border_color': '#000000',  # Black border
    'qr_code_color': '#000000',  # Black QR code
    'qr_code_background': '#FFFFFF',  # White QR background
    
    # Recommended label sizes for QL-820NWB
    'supported_sizes': {
        'small': {'width_mm': 17, 'height_mm': 54},  # 17mm x 54mm
        'medium': {'width_mm': 29, 'height_mm': 90},  # 29mm x 90mm  
        'large': {'width_mm': 38, 'height_mm': 90},   # 38mm x 90mm
        'custom': {'width_mm': 29, 'height_mm': 37}   # Current default
    },
    
    # Font settings optimized for thermal printing
    'font_settings': {
        'base_font_size_ratio': 18,  # Slightly larger for thermal printing
        'large_font_multiplier': 1.6,
        'medium_font_multiplier': 1.3,
        'small_font_multiplier': 0.9,
        'font_family': 'arial.ttf'  # Use Arial for better thermal printing
    },
    
    # QR code settings for thermal printing
    'qr_settings': {
        'size_ratio': 0.45,  # QR code takes 35% of label height
        'error_correction': 'M',  # Medium error correction for thermal printing
        'border': 2  # Border around QR code
    }
}
