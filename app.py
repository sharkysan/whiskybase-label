from flask import Flask, render_template, request, jsonify, send_file
import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
import json
import asyncio
from playwright.async_api import async_playwright
import time
import random
from dotenv import load_dotenv
import config

# Load environment variables from api_config.env if it exists
load_dotenv('api_config.env')

app = Flask(__name__)

class WhiskyLabelGenerator:
    def __init__(self):
        self.base_url = "https://www.whiskybase.com"
        
    async def get_whisky_info_playwright(self, whisky_id):
        """Fetch whisky information using Playwright to call WhiskyBase API endpoint"""
        async with async_playwright() as p:
            # Launch browser with realistic settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with realistic user agent and viewport
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                extra_http_headers={
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'DNT': '1',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            )
            
            page = await context.new_page()
            
            try:
                # First, visit the main site to establish a session and get cookies
                print("Establishing session with WhiskyBase...")
                base_url = os.getenv('WHISKYBASE_BASE_URL', 'https://www.whiskybase.com')
                try:
                    await page.goto(f'{base_url}/', wait_until='domcontentloaded', timeout=10000)
                    await page.wait_for_timeout(2000)  # Wait 2 seconds
                    print("✅ Homepage visited successfully")
                except Exception as e:
                    print(f"Homepage visit failed: {e}, continuing...")
                
                # Build API URL with relations
                api_base_url = os.getenv('WHISKYBASE_API_BASE_URL')
                api_url = f"{api_base_url}/whisky/{whisky_id}?relation[]=brand&relation[]=userrating&relation[]=bottler"
                print(f"Making API request to: {api_url}")
                
                # Make the API request
                timeout_seconds = int(os.getenv('TIMEOUT_SECONDS', 15))
                response = await page.goto(api_url, wait_until='domcontentloaded', timeout=timeout_seconds * 1000)
                print(f"API response status: {response.status}")
                
                if response.status == 200:
                    # Get the JSON content
                    content = await page.content()
                    
                    # Extract JSON from the page content
                    # The response should be pure JSON, but let's handle it carefully
                    try:
                        # Try to parse as JSON directly
                        json_data = await page.evaluate('() => JSON.parse(document.body.textContent)')
                        print(f"✅ API call successful! Response keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dict'}")
                        
                        # Parse the API response
                        whisky_info = self._parse_api_response(json_data, whisky_id)
                        return whisky_info
                        
                    except Exception as e:
                        print(f"Error parsing JSON response: {e}")
                        # Try to extract JSON from the page content manually
                        import re
                        import json
                        
                        # Look for JSON in the page content
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            try:
                                json_data = json.loads(json_match.group())
                                print(f"✅ Extracted JSON from page content")
                                whisky_info = self._parse_api_response(json_data, whisky_id)
                                return whisky_info
                            except Exception as e2:
                                print(f"Error parsing extracted JSON: {e2}")
                        
                        return self._get_fallback_data(whisky_id)
                        
                else:
                    print(f"❌ API request failed with status {response.status}")
                    print(f"Response content: {await response.text()[:300]}...")
                    return self._get_fallback_data(whisky_id)
                
            except Exception as e:
                print(f"Playwright error: {e}")
                return self._get_fallback_data(whisky_id)
            finally:
                await browser.close()
    

    
    def _parse_api_response(self, data, whisky_id):
        """Parse the API response and extract whisky information"""
        try:
            # Handle the real WhiskyBase API response structure
            if 'whisky' in data:
                whisky_data = data['whisky']
            elif 'data' in data:
                whisky_data = data['data']
            else:
                whisky_data = data
            
            # Get name
            name = whisky_data.get('name', f'Whisky #{whisky_id}')
            
            # Get distillery/brand information - try multiple possible fields
            distillery = 'Unknown Distillery'
            if 'brand' in whisky_data and isinstance(whisky_data['brand'], dict):
                # Try brandname first (real API structure), then name
                distillery = whisky_data['brand'].get('brandname') or whisky_data['brand'].get('name', 'Unknown Distillery')
            elif 'brand_name' in whisky_data:
                distillery = whisky_data['brand_name']
            elif 'bottle_for' in whisky_data and whisky_data['bottle_for']:
                # Use bottle_for as distillery name (common in independent bottlings)
                distillery = whisky_data['bottle_for']
            elif 'district' in whisky_data and whisky_data['district']:
                # Use district as fallback (e.g., "Islay" for Islay whiskies)
                distillery = whisky_data['district'] + " Distillery"
            
            # Get ABV/strength
            abv = 'Unknown ABV'
            if 'strength' in whisky_data:
                strength = whisky_data['strength']
                if strength:
                    abv = f"{strength}%"
            elif 'abv' in whisky_data:
                abv_val = whisky_data['abv']
                if abv_val:
                    abv = f"{abv_val}%"
            
            # Get age
            age = ''
            if 'age' in whisky_data and whisky_data['age']:
                age_val = whisky_data['age']
                if age_val:
                    age = f"{age_val} years"
            
            # Get region
            region = 'Unknown Region'
            if 'region' in whisky_data:
                region = whisky_data['region']
            
            # Get bottler information
            bottler = ''
            if 'bottler' in whisky_data and isinstance(whisky_data['bottler'], dict):
                bottler = whisky_data['bottler'].get('name', '')
            elif 'bottler_serie' in whisky_data:
                bottler = whisky_data['bottler_serie']
            
            # Get additional details
            cask_type = whisky_data.get('cask_type', '')
            type_info = whisky_data.get('type', '')
            
            # Build note with additional information
            note_parts = []
            if region and region != 'Unknown Region':
                note_parts.append(region)
            if cask_type:
                note_parts.append(cask_type)
            if bottler:
                note_parts.append(f"Bottled by {bottler}")
            
            note = ' | '.join(note_parts) if note_parts else ''
            
            # Enhanced image extraction for real API response
            image_url = ''
            
            # Try to get image from photos array (real API structure)
            if 'photos' in whisky_data and isinstance(whisky_data['photos'], list):
                photos = whisky_data['photos']
                if photos:
                    # Look for the specific image URL first (479313-normal.png)
                    specific_photo = next((photo for photo in photos if photo.get('id') == 479313), None)
                    if specific_photo:
                        # Use the normal size of the specific photo
                        image_url = specific_photo.get('normal')
                    else:
                        # Look for label photo first (label: true)
                        label_photo = next((photo for photo in photos if photo.get('label', False)), None)
                        if label_photo:
                            # Prefer big size, fall back to normal, then small
                            image_url = label_photo.get('big') or label_photo.get('normal') or label_photo.get('small')
                        else:
                            # Use first photo if no label photo found
                            first_photo = photos[0]
                            image_url = first_photo.get('big') or first_photo.get('normal') or first_photo.get('small')
            
            # Fallback to old image extraction methods
            if not image_url:
                image_data = whisky_data.get('image', {})
                if isinstance(image_data, dict):
                    # Try various possible image URL fields
                    for field in ['url', 'src', 'image_url', 'photo_url', 'thumbnail']:
                        if field in image_data and image_data[field]:
                            image_url = image_data[field]
                            break
                    
                    # If no direct URL, try nested structures
                    if not image_url and 'sizes' in image_data:
                        sizes = image_data['sizes']
                        if isinstance(sizes, dict):
                            # Try to get the largest available size
                            for size in ['large', 'medium', 'small', 'original']:
                                if size in sizes and sizes[size]:
                                    image_url = sizes[size]
                                    break
            
            # If still no image, try alternative image fields in the main data
            if not image_url:
                for field in ['photo', 'picture', 'thumbnail', 'image_url']:
                    if field in whisky_data and whisky_data[field]:
                        image_url = whisky_data[field]
                        break
            
            # Ensure image URL is absolute
            if image_url and not image_url.startswith(('http://', 'https://')):
                base_url = os.getenv('WHISKYBASE_BASE_URL', 'https://www.whiskybase.com')
                image_url = f"{base_url}{image_url}"
            
            return {
                'id': whisky_id,
                'name': name,
                'distillery': distillery,
                'abv': abv,
                'age': age,
                'region': region,
                'note': note,
                'url': f"{os.getenv('WHISKYBASE_BASE_URL', 'https://www.whiskybase.com')}/whisky/{whisky_id}",
                'image_url': image_url,
                'source': 'api'
            }
            
        except Exception as e:
            print(f"Error parsing API response: {e}")
            return self._get_fallback_data(whisky_id)

    def _get_fallback_data(self, whisky_id):
        """Generate fallback data when scraping fails"""
        # Simple fallback data generation
        whiskies = [
            {'name': 'Macallan 18 Year Old', 'distillery': 'The Macallan', 'abv': '43%', 'age': '18 years'},
            {'name': 'Glenfiddich 12 Year Old', 'distillery': 'Glenfiddich', 'abv': '40%', 'age': '12 years'},
            {'name': 'Laphroaig 10 Year Old', 'distillery': 'Laphroaig', 'abv': '43%', 'age': '10 years'},
            {'name': 'Ardbeg Uigeadail', 'distillery': 'Ardbeg', 'abv': '54.2%', 'age': 'No Age Statement'},
            {'name': 'Glenlivet 15 Year Old', 'distillery': 'The Glenlivet', 'abv': '40%', 'age': '15 years'},
            {'name': 'Lagavulin 16 Year Old', 'distillery': 'Lagavulin', 'abv': '43%', 'age': '16 years'},
            {'name': 'Balvenie 12 Year Old', 'distillery': 'The Balvenie', 'abv': '40%', 'age': '12 years'},
            {'name': 'Highland Park 18 Year Old', 'distillery': 'Highland Park', 'abv': '43%', 'age': '18 years'}
        ]
        
        # Use whisky_id to select a whisky (cycling through the list)
        selected_whisky = whiskies[whisky_id % len(whiskies)]
        
        return {
            'id': whisky_id,
            'name': selected_whisky['name'],
            'distillery': selected_whisky['distillery'],
            'abv': selected_whisky['abv'],
            'age': selected_whisky['age'],
            'image_url': None,  # No image for fallback data
            'url': f"{os.getenv('WHISKYBASE_BASE_URL', 'https://www.whiskybase.com')}/whisky/{whisky_id}",
            'source': 'fallback_data',
            'note': 'Data from fallback source (Whiskybase unavailable)'
        }
    
    def get_whisky_info(self, whisky_id):
        """Synchronous wrapper for async Playwright method"""
        try:
            # Run the async method in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.get_whisky_info_playwright(whisky_id))
            loop.close()
            return result
        except Exception as e:
            print(f"Error in get_whisky_info: {e}")
            return self._get_fallback_data(whisky_id)

    def create_qr_code(self, url, filename="qr_code.png"):
        """Create QR code for the whisky URL"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        qr_image.save(filename)
        return filename

    def create_label(self, whisky_info, output_filename="whisky_label.png", width_mm=35, height_mm=37, dpi=72):
        """Create a whisky label with QR code"""
        # Convert mm to pixels
        # For screen display, use 72 DPI (standard screen resolution)
        # For print quality, use 300 DPI
        pixels_per_mm = dpi / 25.4
        
        width = int(width_mm * pixels_per_mm)
        height = int(height_mm * pixels_per_mm)
        
        # Create image with white background
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Add small border inside the label
        border_width = max(1, width // 200)  # Border width proportional to label size
        draw.rectangle([border_width, border_width, width - border_width, height - border_width], 
                      outline='#CCCCCC', width=border_width)
        
        # Calculate proportional font sizes based on label dimensions
        # Make fonts smaller to fit all content
        base_font_size = min(width, height) // 16  # Smaller base font
        font_large_size = int(base_font_size * 1.5)  # Smaller multiplier
        font_medium_size = int(base_font_size * 1.2)  # Smaller multiplier
        font_small_size = int(base_font_size * 0.9)  # Smaller multiplier
        
        try:
            # Try to load a font, fall back to default if not available
            font_large = ImageFont.truetype("arial.ttf", font_large_size)
            font_medium = ImageFont.truetype("arial.ttf", font_medium_size)
            font_small = ImageFont.truetype("arial.ttf", font_small_size)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Create QR code
        qr_filename = self.create_qr_code(whisky_info['url'])
        qr_image = Image.open(qr_filename)
        
        # Resize QR code to fill the top portion of the label
        # Use 50% of the label height for QR code to make it more prominent
        qr_size = min(width, int(height * 0.4))
        qr_image = qr_image.resize((qr_size, qr_size))
        
        # Position QR code centered at the top (accounting for border)
        qr_x = (width - qr_size) // 2  # Center horizontally
        qr_y = border_width + (height - border_width * 2) // config.MARGIN_RATIO  # Margin from top, inside border
        image.paste(qr_image, (qr_x, qr_y))
        
        # Add text content - start below QR code (accounting for border)
        y_position = qr_y + qr_size + (height // (config.MARGIN_RATIO * 2))  # Start below QR code with smaller margin
        line_height = max(font_large_size + 1, height // 15)  # Use font height + minimal padding, minimum 1/15 of label height
        
        # Whisky name
        name = whisky_info['name']
        max_name_length = width // (font_large_size // 2)  # Approximate characters that fit
        if len(name) > max_name_length:
            name = name[:max_name_length-3] + "..."
        
        # Center the text (accounting for border)
        bbox = draw.textbbox((0, 0), name, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, y_position), name, fill='black', font=font_large)
        y_position += line_height
        
        # Distillery
        distillery = whisky_info['distillery']
        max_distillery_length = width // (font_medium_size // 2)  # Approximate characters that fit
        if len(distillery) > max_distillery_length:
            distillery = distillery[:max_distillery_length-3] + "..."
        
        distillery_text = f"Distillery: {distillery}"
        bbox = draw.textbbox((0, 0), distillery_text, font=font_medium)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, y_position), distillery_text, fill='black', font=font_medium)
        y_position += line_height
        
        # ABV
        abv = whisky_info.get('abv', 'Unknown ABV')
        abv_text = f"ABV: {abv}"
        bbox = draw.textbbox((0, 0), abv_text, font=font_medium)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, y_position), abv_text, fill='black', font=font_medium)
        y_position += line_height
        
        # Age
        if whisky_info.get('age'):
            age = whisky_info['age']
            age_text = f"Age: {age}"
            bbox = draw.textbbox((0, 0), age_text, font=font_medium)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            draw.text((text_x, y_position), age_text, fill='black', font=font_medium)
            y_position += line_height
        
        # Source note
        if whisky_info.get('note'):
            note = whisky_info['note']
            bbox = draw.textbbox((0, 0), note, font=font_small)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            draw.text((text_x, y_position), note, fill='black', font=font_small)
            y_position += line_height
        
        # Whisky ID
        id_text = f"ID: {whisky_info['id']}"
        bbox = draw.textbbox((0, 0), id_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, y_position), id_text, fill='black', font=font_small)
        
        # Save the label
        image.save(output_filename)
        
        # Clean up QR code file
        if os.path.exists(qr_filename):
            os.remove(qr_filename)
        
        return output_filename

    def create_ql820nwb_label(self, whisky_info, output_filename="whisky_label_ql820nwb.png", size_preset='custom'):
        """Create a whisky label optimized for Brother QL-820NWB thermal printer"""
        # Get QL-820NWB settings
        ql_settings = config.QL820NWB_SETTINGS
        
        # Get label dimensions based on preset
        if size_preset in ql_settings['supported_sizes']:
            width_mm = ql_settings['supported_sizes'][size_preset]['width_mm']
            height_mm = ql_settings['supported_sizes'][size_preset]['height_mm']
        else:
            # Use custom size
            width_mm = ql_settings['supported_sizes']['custom']['width_mm']
            height_mm = ql_settings['supported_sizes']['custom']['height_mm']
        
        # Use QL-820NWB optimized DPI
        dpi = ql_settings['dpi']
        pixels_per_mm = dpi / 25.4
        
        width = int(width_mm * pixels_per_mm)
        height = int(height_mm * pixels_per_mm)
        
        # Create image with pure white background for thermal printing
        image = Image.new('RGB', (width, height), color=ql_settings['background_color'])
        draw = ImageDraw.Draw(image)
        
        # Add black border for thermal printing
        border_width = max(2, width // 150)  # Slightly thicker border for thermal printing
        draw.rectangle([border_width, border_width, width - border_width, height - border_width], 
                      outline=ql_settings['border_color'], width=border_width)
        
        # Calculate font sizes optimized for thermal printing
        font_settings = ql_settings['font_settings']
        base_font_size = min(width, height) // font_settings['base_font_size_ratio']
        font_large_size = int(base_font_size * font_settings['large_font_multiplier'])
        font_medium_size = int(base_font_size * font_settings['medium_font_multiplier'])
        font_small_size = int(base_font_size * font_settings['small_font_multiplier'])
        
        try:
            # Try to load Arial font for better thermal printing
            font_large = ImageFont.truetype(font_settings['font_family'], font_large_size)
            font_medium = ImageFont.truetype(font_settings['font_family'], font_medium_size)
            font_small = ImageFont.truetype(font_settings['font_family'], font_small_size)
        except:
            # Fall back to default font
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Create QR code optimized for thermal printing
        qr_settings = ql_settings['qr_settings']
        qr_filename = self.create_qr_code_thermal(whisky_info['url'], qr_settings)
        qr_image = Image.open(qr_filename)
        
        # Resize QR code based on thermal printing settings
        qr_size = min(width, int(height * qr_settings['size_ratio']))
        qr_image = qr_image.resize((qr_size, qr_size))
        
        # Position QR code centered at the top
        qr_x = (width - qr_size) // 2
        qr_y = border_width * 2  # More margin for thermal printing
        image.paste(qr_image, (qr_x, qr_y))
        
        # Add text content - start below QR code
        y_position = qr_y + qr_size + (height // 25)  # More spacing for thermal printing
        line_height = max(font_large_size + 2, height // 12)  # More line height for thermal printing
        
        # Whisky name
        name = whisky_info['name']
        max_name_length = width // (font_large_size // 3)  # More conservative character limit
        if len(name) > max_name_length:
            name = name[:max_name_length-3] + "..."
        
        # Center the text
        bbox = draw.textbbox((0, 0), name, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, y_position), name, fill=ql_settings['text_color'], font=font_large)
        y_position += line_height
        
        # Distillery
        distillery = whisky_info['distillery']
        max_distillery_length = width // (font_medium_size // 3)
        if len(distillery) > max_distillery_length:
            distillery = distillery[:max_distillery_length-3] + "..."
        
        distillery_text = f"Distillery: {distillery}"
        bbox = draw.textbbox((0, 0), distillery_text, font=font_medium)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, y_position), distillery_text, fill=ql_settings['text_color'], font=font_medium)
        y_position += line_height
        
        # ABV
        abv = whisky_info.get('abv', 'Unknown ABV')
        abv_text = f"ABV: {abv}"
        bbox = draw.textbbox((0, 0), abv_text, font=font_medium)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, y_position), abv_text, fill=ql_settings['text_color'], font=font_medium)
        y_position += line_height
        
        # Age
        if whisky_info.get('age'):
            age = whisky_info['age']
            age_text = f"Age: {age}"
            bbox = draw.textbbox((0, 0), age_text, font=font_medium)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            draw.text((text_x, y_position), age_text, fill=ql_settings['text_color'], font=font_medium)
            y_position += line_height
        
        # Whisky ID
        id_text = f"ID: {whisky_info['id']}"
        bbox = draw.textbbox((0, 0), id_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, y_position), id_text, fill=ql_settings['text_color'], font=font_small)
        
        # Save the label
        image.save(output_filename, 'PNG', dpi=(dpi, dpi))
        
        # Clean up QR code file
        if os.path.exists(qr_filename):
            os.remove(qr_filename)
        
        return output_filename

    def create_qr_code_thermal(self, url, qr_settings):
        """Create QR code optimized for thermal printing"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{qr_settings["error_correction"]}'),
            box_size=qr_settings['border'],
            border=qr_settings['border']
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create QR code image with black on white for thermal printing
        qr_image = qr.make_image(fill_color='black', back_color='white')
        qr_filename = f"qr_thermal_{int(time.time())}.png"
        qr_image.save(qr_filename)
        
        return qr_filename

# Initialize the generator
generator = WhiskyLabelGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_label():
    whisky_id = request.form.get('whisky_id', type=int)
    whisky_name = request.form.get('whisky_name', '').strip()
    distillery = request.form.get('distillery', '').strip()
    abv = request.form.get('abv', '').strip()
    age = request.form.get('age', '').strip()
    
    # Get label size parameters (default to 35mm x 37mm)
    width_mm = request.form.get('width_mm', type=float, default=35.0)
    height_mm = request.form.get('height_mm', type=float, default=37.0)
    dpi = request.form.get('dpi', type=int, default=72)  # 72 DPI for screen, 300 for print
    
    if whisky_name and distillery and abv:
        # Use manual data if provided
        whisky_info = {
            'id': whisky_id or 0,
            'name': whisky_name,
            'distillery': distillery,
            'abv': abv,
            'age': age,
            'url': f"{os.getenv('WHISKYBASE_BASE_URL', 'https://www.whiskybase.com')}/whisky/{whisky_id or 0}",
            'source': 'manual_input'
        }
    elif whisky_id:
        # Fetch from Whiskybase
        whisky_info = generator.get_whisky_info(whisky_id)
    else:
        return jsonify({'error': 'Please provide either a Whiskybase ID or manual whisky details (name, distillery, and ABV)'}), 400
    
    # Generate label
    label_filename = generator.create_label(whisky_info, width_mm=width_mm, height_mm=height_mm, dpi=dpi)
    
    return send_file(label_filename, mimetype='image/png')

@app.route('/api/label/<int:whisky_id>')
def api_label(whisky_id):
    """API endpoint to generate label for a specific whisky ID"""
    whisky_info = generator.get_whisky_info(whisky_id)
    
    # Get label size parameters from query string (default to 35mm x 37mm)
    width_mm = request.args.get('width_mm', type=float, default=35.0)
    height_mm = request.args.get('height_mm', type=float, default=37.0)
    dpi = request.args.get('dpi', type=int, default=72)  # 72 DPI for screen, 300 for print
    
    label_filename = generator.create_label(whisky_info, width_mm=width_mm, height_mm=height_mm, dpi=dpi)
    return send_file(label_filename, mimetype='image/png')

@app.route('/api/custom-label', methods=['POST', 'GET'])
def api_custom_label():
    """API endpoint to generate label with custom data"""
    if request.method == 'POST':
        data = request.get_json()
    else:
        # Handle GET request with query parameters
        data = {
            'name': request.args.get('name'),
            'distillery': request.args.get('distillery'),
            'abv': request.args.get('abv'),
            'age': request.args.get('age'),
            'id': request.args.get('id')
        }
    
    # Get label size parameters (default to 35mm x 37mm)
    width_mm = request.args.get('width_mm', type=float, default=35.0)
    height_mm = request.args.get('height_mm', type=float, default=37.0)
    dpi = request.args.get('dpi', type=int, default=72)  # 72 DPI for screen, 300 for print
    
    if not data or not data.get('name') or not data.get('distillery'):
        return jsonify({'error': 'Name and distillery are required'}), 400
    
    whisky_info = {
        'id': data.get('id', 0),
        'name': data['name'],
        'distillery': data['distillery'],
        'abv': data.get('abv', 'Unknown ABV'),
        'age': data.get('age', ''),
        'url': f"{os.getenv('WHISKYBASE_BASE_URL', 'https://www.whiskybase.com')}/whisky/{data.get('id', 0)}",
        'source': 'api_custom'
    }
    
    label_filename = generator.create_label(whisky_info, width_mm=width_mm, height_mm=height_mm, dpi=dpi)
    return send_file(label_filename, mimetype='image/png')

@app.route('/api/ql820nwb/<int:whisky_id>')
def api_ql820nwb_label(whisky_id):
    """API endpoint to generate label optimized for Brother QL-820NWB printer"""
    whisky_info = generator.get_whisky_info(whisky_id)
    
    # Get size preset from query string (default to 'custom')
    size_preset = request.args.get('size', default='custom')
    
    label_filename = generator.create_ql820nwb_label(whisky_info, size_preset=size_preset)
    return send_file(label_filename, mimetype='image/png')

@app.route('/api/ql820nwb/custom', methods=['POST', 'GET'])
def api_ql820nwb_custom_label():
    """API endpoint to generate QL-820NWB optimized label with custom data"""
    if request.method == 'POST':
        data = request.get_json()
    else:
        # Handle GET request with query parameters
        data = {
            'name': request.args.get('name'),
            'distillery': request.args.get('distillery'),
            'abv': request.args.get('abv'),
            'age': request.args.get('age'),
            'id': request.args.get('id')
        }
    
    # Get size preset from query string (default to 'custom')
    size_preset = request.args.get('size', default='custom')
    
    if not data or not data.get('name') or not data.get('distillery'):
        return jsonify({'error': 'Name and distillery are required'}), 400
    
    whisky_info = {
        'id': data.get('id', 0),
        'name': data['name'],
        'distillery': data['distillery'],
        'abv': data.get('abv', 'Unknown ABV'),
        'age': data.get('age', ''),
        'url': f"{os.getenv('WHISKYBASE_BASE_URL', 'https://www.whiskybase.com')}/whisky/{data.get('id', 0)}",
        'source': 'api_custom'
    }
    
    label_filename = generator.create_ql820nwb_label(whisky_info, size_preset=size_preset)
    return send_file(label_filename, mimetype='image/png')

@app.route('/api/whisky/<int:whisky_id>')
def api_whisky(whisky_id):
    """API endpoint to get whisky information"""
    whisky_info = generator.get_whisky_info(whisky_id)
    return jsonify(whisky_info)

@app.route('/debug/whisky/<int:whisky_id>')
def debug_whisky(whisky_id):
    """Debug endpoint to see raw whisky data"""
    whisky_info = generator.get_whisky_info(whisky_id)
    return jsonify(whisky_info)

@app.route('/api/print/<int:whisky_id>')
def api_print_label(whisky_id):
    """API endpoint to print label directly (opens print dialog)"""
    whisky_info = generator.get_whisky_info(whisky_id)
    
    # Get parameters
    printer_type = request.args.get('printer_type', default='standard')
    size_preset = request.args.get('size', default='custom')
    width_mm = request.args.get('width_mm', type=float, default=35.0)
    height_mm = request.args.get('height_mm', type=float, default=37.0)
    dpi = request.args.get('dpi', type=int, default=72)
    
    # Generate appropriate label
    if printer_type == 'ql820nwb':
        label_filename = generator.create_ql820nwb_label(whisky_info, size_preset=size_preset)
    else:
        label_filename = generator.create_label(whisky_info, width_mm=width_mm, height_mm=height_mm, dpi=dpi)
    
    # Return HTML page that auto-prints
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Print Whisky Label</title>
        <style>
            body {{ margin: 0; padding: 20px; text-align: center; }}
            .label-container {{ display: inline-block; }}
            .print-button {{ 
                margin: 20px; 
                padding: 10px 20px; 
                background: #27ae60; 
                color: white; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="label-container">
            <img src="/{label_filename}" alt="Whisky Label" style="max-width: 100%; height: auto;">
        </div>
        <br>
        <button class="print-button" onclick="window.print()">🖨️ Print Label</button>
        <script>
            // Auto-print after page loads
            window.onload = function() {{
                setTimeout(function() {{
                    window.print();
                }}, 1000);
            }};
        </script>
    </body>
    </html>
    """
    
    return html_content

@app.route('/api/batch-labels', methods=['POST'])
def api_batch_labels():
    """API endpoint for generating multiple labels from a list of IDs"""
    try:
        data = request.get_json()
        
        # Extract parameters
        whisky_ids = data.get('whisky_ids', [])
        width_mm = int(data.get('width_mm', 35))
        height_mm = int(data.get('height_mm', 37))
        dpi = int(data.get('dpi', 72))
        printer_type = data.get('printer_type', 'standard')
        ql820nwb_size = data.get('ql820nwb_size', 'custom')
        
        if not whisky_ids:
            return jsonify({'error': 'No whisky IDs provided'}), 400
        
        generator = WhiskyLabelGenerator()
        generated_files = []
        
        for whisky_id in whisky_ids:
            try:
                # Get whisky info
                whisky_info = generator.get_whisky_info(whisky_id)
                
                # Generate label based on printer type
                if printer_type == 'ql820nwb':
                    output_filename = f"whisky_{whisky_id}_ql820nwb_{int(time.time())}.png"
                    generator.create_ql820nwb_label(whisky_info, output_filename, size_preset=ql820nwb_size)
                else:
                    output_filename = f"whisky_{whisky_id}_label_{int(time.time())}.png"
                    generator.create_label(whisky_info, output_filename, width_mm, height_mm, dpi)
                
                generated_files.append({
                    'whisky_id': whisky_id,
                    'filename': output_filename,
                    'whisky_info': whisky_info
                })
                
            except Exception as e:
                generated_files.append({
                    'whisky_id': whisky_id,
                    'error': str(e),
                    'filename': None
                })
        
        # Create a ZIP file with all labels
        import zipfile
        import os
        
        zip_filename = f"batch_labels_{int(time.time())}.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file_info in generated_files:
                if file_info.get('filename') and os.path.exists(file_info['filename']):
                    zipf.write(file_info['filename'], os.path.basename(file_info['filename']))
        
        return send_file(zip_filename, mimetype='application/zip', as_attachment=True, download_name=zip_filename)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
