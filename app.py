from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)

class WhiskyLabelGenerator:
    def __init__(self):
        self.base_url = "https://www.whiskybase.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def get_whisky_info(self, whisky_id):
        """Fetch whisky information from Whiskybase"""
        try:
            url = f"{self.base_url}/whisky/{whisky_id}"
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 403:
                # If we get blocked, return a generic label with the ID
                return {
                    'id': whisky_id,
                    'name': f"Whisky #{whisky_id}",
                    'distillery': "Whiskybase",
                    'region': "Online Database",
                    'age': "",
                    'url': url,
                    'note': "Data unavailable due to access restrictions"
                }
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract whisky name - try multiple selectors
            name_elem = soup.find('h1', class_='whisky-name')
            if not name_elem:
                name_elem = soup.find('h1')
            if not name_elem:
                name_elem = soup.find('title')
            
            name = name_elem.get_text(strip=True) if name_elem else f"Whisky #{whisky_id}"
            
            # Extract distillery
            distillery_elem = soup.find('a', href=lambda x: x and '/distillery/' in x)
            distillery = distillery_elem.get_text(strip=True) if distillery_elem else "Unknown Distillery"
            
            # Extract region
            region_elem = soup.find('a', href=lambda x: x and '/region/' in x)
            region = region_elem.get_text(strip=True) if region_elem else "Unknown Region"
            
            # Extract age if available
            age_elem = soup.find('span', string=lambda x: x and 'year' in x.lower())
            if not age_elem:
                age_elem = soup.find(string=lambda x: x and 'year' in x.lower())
            age = age_elem.get_text(strip=True) if age_elem else ""
            
            return {
                'id': whisky_id,
                'name': name,
                'distillery': distillery,
                'region': region,
                'age': age,
                'url': url
            }
        except requests.exceptions.RequestException as e:
            return {
                'id': whisky_id,
                'name': f"Whisky #{whisky_id}",
                'distillery': "Whiskybase",
                'region': "Online Database",
                'age': "",
                'url': f"{self.base_url}/whisky/{whisky_id}",
                'note': f"Network error: {str(e)}"
            }
        except Exception as e:
            return {
                'id': whisky_id,
                'name': f"Whisky #{whisky_id}",
                'distillery': "Whiskybase",
                'region': "Online Database",
                'age': "",
                'url': f"{self.base_url}/whisky/{whisky_id}",
                'note': f"Error: {str(e)}"
            }
    
    def generate_qr_code(self, whisky_id, size=200):
        """Generate QR code for the whisky ID"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"https://www.whiskybase.com/whisky/{whisky_id}")
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((size, size))
        
        return qr_img
    
    def create_label(self, whisky_info, label_size=(400, 600)):
        """Create a whisky label with QR code and information"""
        # Create a new image with white background
        img = Image.new('RGB', label_size, 'white')
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to load a nice font, fallback to default if not available
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_medium = ImageFont.truetype("arial.ttf", 18)
            font_small = ImageFont.truetype("arial.ttf", 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Add border
        draw.rectangle([(10, 10), (label_size[0]-10, label_size[1]-10)], outline='black', width=2)
        
        # Add title
        title = "WHISKY LABEL"
        title_bbox = draw.textbbox((0, 0), title, font=font_large)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((label_size[0] - title_width) // 2, 30), title, fill='black', font=font_large)
        
        # Add whisky name
        name = whisky_info['name']
        if len(name) > 30:
            name = name[:27] + "..."
        draw.text((20, 80), f"Name: {name}", fill='black', font=font_medium)
        
        # Add distillery
        distillery = whisky_info['distillery']
        if len(distillery) > 25:
            distillery = distillery[:22] + "..."
        draw.text((20, 110), f"Distillery: {distillery}", fill='black', font=font_medium)
        
        # Add region
        region = whisky_info['region']
        if len(region) > 25:
            region = region[:22] + "..."
        draw.text((20, 140), f"Region: {region}", fill='black', font=font_medium)
        
        # Add age if available
        if whisky_info['age']:
            age = whisky_info['age']
            if len(age) > 25:
                age = age[:22] + "..."
            draw.text((20, 170), f"Age: {age}", fill='black', font=font_medium)
        
        # Add whisky ID
        draw.text((20, 200), f"ID: {whisky_info['id']}", fill='black', font=font_small)
        
        # Add note if available (for error cases)
        if 'note' in whisky_info:
            note = whisky_info['note']
            if len(note) > 35:
                note = note[:32] + "..."
            draw.text((20, 230), f"Note: {note}", fill='red', font=font_small)
        
        # Generate and add QR code
        qr_img = self.generate_qr_code(whisky_info['id'], 150)
        qr_x = (label_size[0] - 150) // 2
        qr_y = 280 if 'note' in whisky_info else 250
        img.paste(qr_img, (qr_x, qr_y))
        
        # Add scan instruction
        scan_text = "Scan for details"
        scan_bbox = draw.textbbox((0, 0), scan_text, font=font_small)
        scan_width = scan_bbox[2] - scan_bbox[0]
        draw.text(((label_size[0] - scan_width) // 2, qr_y + 160), scan_text, fill='black', font=font_small)
        
        return img

# Initialize the label generator
label_generator = WhiskyLabelGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/whisky/<int:whisky_id>')
def get_whisky(whisky_id):
    """API endpoint to get whisky information"""
    whisky_info = label_generator.get_whisky_info(whisky_id)
    return jsonify(whisky_info)

@app.route('/api/label/<int:whisky_id>')
def generate_label(whisky_id):
    """API endpoint to generate and return a label image"""
    whisky_info = label_generator.get_whisky_info(whisky_id)
    label_img = label_generator.create_label(whisky_info)
    
    # Convert PIL image to bytes
    img_io = io.BytesIO()
    label_img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

@app.route('/generate', methods=['POST'])
def generate_label_web():
    """Web endpoint to generate label from form"""
    whisky_id = request.form.get('whisky_id')
    if not whisky_id:
        return jsonify({'error': 'Whisky ID is required'}), 400
    
    try:
        whisky_id = int(whisky_id)
    except ValueError:
        return jsonify({'error': 'Invalid Whisky ID'}), 400
    
    whisky_info = label_generator.get_whisky_info(whisky_id)
    label_img = label_generator.create_label(whisky_info)
    
    # Convert PIL image to bytes
    img_io = io.BytesIO()
    label_img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
