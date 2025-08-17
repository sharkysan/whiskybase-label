# 🥃 Whisky Label Generator

A beautiful web application that generates custom labels for whisky bottles with QR codes by fetching data from Whiskybase.

## Features

- **Whisky Data Fetching**: Automatically retrieves whisky information from Whiskybase using the whisky ID
- **QR Code Generation**: Creates QR codes that link directly to the Whiskybase page
- **Custom Label Design**: Generates professional-looking labels with whisky details
- **Modern Web Interface**: Responsive design that works on desktop and mobile devices
- **Real-time Preview**: See the generated label instantly in the browser

## What's Included

- **Whisky Name**: The official name from Whiskybase
- **Distillery**: The distillery that produced the whisky
- **Region**: The whisky region (e.g., Speyside, Islay, Highland)
- **Age Statement**: Age information if available
- **Whisky ID**: The unique identifier from Whiskybase
- **QR Code**: Scannable code that links to the full Whiskybase page

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd baselabel
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

## How to Use

1. **Find a Whisky ID**: 
   - Go to [Whiskybase.com](https://www.whiskybase.com)
   - Search for your whisky
   - Copy the ID from the URL (e.g., `https://www.whiskybase.com/whisky/12345` → ID is `12345`)

2. **Generate a Label**:
   - Enter the whisky ID in the input field
   - Click "Generate Label"
   - The application will fetch the whisky data and create a custom label

3. **Download the Label**:
   - Right-click on the generated label image
   - Select "Save image as..." to download it
   - Print the label and attach it to your whisky bottle

## API Endpoints

The application also provides REST API endpoints for programmatic access:

- `GET /api/whisky/{id}` - Get whisky information
- `GET /api/label/{id}` - Generate and return label image
- `POST /generate` - Generate label from form data

## Example Usage

```python
import requests

# Get whisky information
response = requests.get('http://localhost:5000/api/whisky/12345')
whisky_data = response.json()
print(whisky_data)

# Get label image
response = requests.get('http://localhost:5000/api/label/12345')
with open('whisky_label.png', 'wb') as f:
    f.write(response.content)
```

## Technical Details

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Image Generation**: Pillow (PIL)
- **QR Code**: qrcode library
- **Web Scraping**: BeautifulSoup4
- **HTTP Requests**: requests library

## Label Specifications

- **Size**: 400x600 pixels
- **Format**: PNG
- **Background**: White
- **Border**: Black outline
- **QR Code Size**: 150x150 pixels
- **Font**: Arial (fallback to system default)

## Troubleshooting

### Common Issues

1. **"Failed to fetch whisky data"**
   - Check if the whisky ID is correct
   - Ensure you have an internet connection
   - The whisky might not exist on Whiskybase

2. **"Invalid Whisky ID"**
   - Make sure you're entering a number
   - Whisky IDs are typically 5-6 digit numbers

3. **Font not loading**
   - The application will fall back to system default fonts
   - This doesn't affect functionality

### Rate Limiting

The application respects Whiskybase's servers by:
- Using appropriate headers
- Implementing timeouts
- Not making excessive requests

## Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Improving the label design
- Adding support for other whisky databases

## License

This project is open source and available under the MIT License.

## Disclaimer

This application is for personal use only. Please respect Whiskybase's terms of service and don't use this for commercial purposes without permission.

---

**Enjoy your whisky collection! 🥃**
