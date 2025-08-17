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

load_dotenv()

app = Flask(__name__)

class WhiskyLabelGenerator:
    def __init__(self):
        self.base_url = "https://www.whiskybase.com"
        
    async def get_whisky_info_playwright(self, whisky_id):
        """Fetch whisky information using Playwright (headless browser)"""
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
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'DNT': '1'
                }
            )
            
            page = await context.new_page()
            
            try:
                # Try to visit the homepage first (with shorter timeout)
                print(f"Visiting homepage...")
                try:
                    await page.goto(self.base_url, wait_until='domcontentloaded', timeout=15000)
                    await page.wait_for_timeout(1000)  # Wait 1 second
                except Exception as e:
                    print(f"Homepage visit failed: {e}, continuing...")
                
                # Try different URL patterns
                url_patterns = [
                    f"{self.base_url}/whiskies/whisky/{whisky_id}",
                    f"{self.base_url}/whisky/{whisky_id}"
                ]
                
                response = None
                final_url = None
                
                for url in url_patterns:
                    print(f"Trying URL: {url}")
                    try:
                        response = await page.goto(url, wait_until='domcontentloaded', timeout=2000)
                        print(f"Response status: {response.status}")
                        
                        if response.status == 200:
                            print(f"✅ Success with URL: {url}")
                            final_url = url
                            break
                        elif response.status == 403:
                            print(f"❌ 403 Forbidden with URL: {url}")
                            continue
                        else:
                            print(f"❌ Status {response.status} with URL: {url}")
                            continue
                    except Exception as e:
                        print(f"Error with URL {url}: {e}")
                        continue
                
                if not final_url:
                    print("All URLs failed, returning fallback data...")
                    return self._get_fallback_data(whisky_id)
                
                # Wait for content to load
                await page.wait_for_timeout(3000)
                
                # Get page content
                content = await page.content()
                
                # Extract whisky information
                whisky_info = await self._extract_whisky_info(page, whisky_id, final_url)
                
                return whisky_info
                
            except Exception as e:
                print(f"Playwright error: {e}")
                return self._get_fallback_data(whisky_id)
            finally:
                await browser.close()
    
    async def _extract_whisky_info(self, page, whisky_id, url):
        """Extract whisky information from the page"""
        try:
            # Get page title
            title = await page.title()
            print(f"Page title: {title}")
            
            # Check if page is valid
            if 'not found' in title.lower() or '404' in title.lower():
                print("Page appears to be 'not found', using fallback data...")
                return self._get_fallback_data(whisky_id)
            
            # Extract name
            name = f"Whisky #{whisky_id}"
            try:
                name_elem = await page.query_selector('h1.whisky-name')
                if name_elem:
                    name = await name_elem.text_content()
                    name = ' '.join(name.split())  # Remove extra whitespace and newlines
                else:
                    # Try alternative selectors
                    name_elem = await page.query_selector('h1')
                    if name_elem:
                        name = await name_elem.text_content()
                        name = ' '.join(name.split())  # Remove extra whitespace and newlines
                    elif 'whisky' in title.lower():
                        name = title.replace('Whiskybase - ', '').strip()
            except:
                pass
            
            # Extract distillery
            distillery = "Unknown Distillery"
            try:
                distillery_elem = await page.query_selector('a[href*="/distillery/"]')
                if distillery_elem:
                    distillery = await distillery_elem.text_content()
                    distillery = ' '.join(distillery.split())  # Remove extra whitespace and newlines
            except:
                pass
            
            # Extract ABV
            abv = "Unknown ABV"
            try:
                # Look for ABV information in various formats
                abv_selectors = [
                    'text=/\\d+(\\.\\d+)?\\s*%/i',
                    'text=/\\d+(\\.\\d+)?\\s*abv/i',
                    'text=/\\d+(\\.\\d+)?\\s*vol/i'
                ]
                
                for selector in abv_selectors:
                    abv_elem = await page.query_selector(selector)
                    if abv_elem:
                        abv_text = await abv_elem.text_content()
                        abv = ' '.join(abv_text.split()).strip()
                        break
                        
                # If no ABV found with selectors, try to find it in the page content
                if abv == "Unknown ABV":
                    # Look for common ABV patterns in the page
                    page_content = await page.content()
                    import re
                    abv_patterns = [
                        r'(\d+(?:\.\d+)?)\s*%',
                        r'(\d+(?:\.\d+)?)\s*ABV',
                        r'(\d+(?:\.\d+)?)\s*vol'
                    ]
                    
                    for pattern in abv_patterns:
                        match = re.search(pattern, page_content, re.IGNORECASE)
                        if match:
                            abv = f"{match.group(1)}%"
                            break
            except:
                pass
            
            # Extract age
            age = ""
            try:
                # Look for age information in various formats
                age_selectors = [
                    'text=/\\d+\\s*year/i',
                    'text=/\\d+\\s*yo/i',
                    'text=/\\d+\\s*yr/i'
                ]
                
                for selector in age_selectors:
                    age_elem = await page.query_selector(selector)
                    if age_elem:
                        age_text = await age_elem.text_content()
                        age = age_text.strip()
                        break
            except:
                pass
            
            return {
                'id': whisky_id,
                'name': name,
                'distillery': distillery,
                'abv': abv,
                'age': age,
                'url': url,
                'source': 'whiskybase_playwright'
            }
            
        except Exception as e:
            print(f"Error extracting whisky info: {e}")
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
            'url': f"{self.base_url}/whisky/{whisky_id}",
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
            box_size=10,
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
        # Use 30% of the label height for QR code to leave more room for text
        qr_size = min(width, int(height * 0.3))
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
            'url': f"https://www.whiskybase.com/whisky/{whisky_id or 0}",
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
        'url': f"https://www.whiskybase.com/whisky/{data.get('id', 0)}",
        'source': 'api_custom'
    }
    
    label_filename = generator.create_label(whisky_info, width_mm=width_mm, height_mm=height_mm, dpi=dpi)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
