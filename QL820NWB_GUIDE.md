# Brother QL-820NWB Printer Guide

## 🖨️ QL-820NWB Thermal Printer Setup

Your whisky label generator now includes specialized support for the **Brother QL-820NWB** thermal printer. This guide will help you set up and use the printer for optimal label printing.

## 📋 Printer Specifications

- **Type**: Thermal printer
- **Resolution**: 300 DPI
- **Label Width**: 12mm to 62mm
- **Connection**: USB, Network (Wi-Fi)
- **Supported Label Sizes**: Small, Medium, Large, Custom

## 🏷️ Supported Label Sizes

| Size | Dimensions | Use Case |
|------|------------|----------|
| **Small** | 17mm x 54mm | Mini bottles, sample labels |
| **Medium** | 29mm x 90mm | Standard bottles, most common |
| **Large** | 38mm x 90mm | Premium bottles, detailed labels |
| **Custom** | 35mm x 37mm | Default size, customizable |

## 🚀 Quick Start

### 1. Web Interface
1. Open your browser and go to `http://localhost:5000`
2. Select **"Brother QL-820NWB (Thermal)"** from the Printer Type dropdown
3. Choose your preferred label size
4. Enter whisky details or WhiskyBase ID
5. Click **"Generate Label"**
6. The optimized label will download automatically

### 2. API Endpoints

#### Generate QL-820NWB Label from WhiskyBase ID:
```
GET /api/ql820nwb/{whisky_id}?size={size_preset}
```

**Example:**
```
http://localhost:5000/api/ql820nwb/12345?size=medium
```

#### Generate QL-820NWB Label with Custom Data:
```
GET /api/ql820nwb/custom?name={name}&distillery={distillery}&abv={abv}&age={age}&size={size_preset}
```

**Example:**
```
http://localhost:5000/api/ql820nwb/custom?name=Macallan%2018&distillery=The%20Macallan&abv=43%25&age=18%20years&size=large
```

#### Print Label Directly:
```
GET /api/print/{whisky_id}?printer_type=ql820nwb&size={size_preset}
```

**Example:**
```
http://localhost:5000/api/print/12345?printer_type=ql820nwb&size=medium
```

This endpoint opens a print dialog automatically with the generated label.

## 🎨 Label Optimization Features

### Thermal Printing Optimizations:
- **Pure black text** on white background for maximum contrast
- **300 DPI resolution** for crisp thermal printing
- **Optimized font sizes** for thermal printer readability
- **Enhanced QR codes** with medium error correction
- **Thicker borders** for better definition

### Color Scheme:
- **Background**: Pure white (#FFFFFF)
- **Text**: Pure black (#000000)
- **Borders**: Pure black (#000000)
- **QR Code**: Black on white

## 🖥️ Printer Setup

### 1. Install Brother QL Software
1. Download **Brother QL Software** from Brother's website
2. Install the software on your computer
3. Connect your QL-820NWB printer via USB or network

### 2. Configure Printer Settings
1. Open **Brother QL Software**
2. Set **Label Size** to match your chosen size
3. Set **Print Quality** to **300 DPI**
4. Enable **Auto Cut** if available

### 3. Load Labels
1. Use **Brother QL labels** for best results
2. Ensure labels are properly aligned
3. Test print a sample label

## 📱 Printing Workflow

### Method 1: Direct Print (Recommended)
1. Generate label using web interface
2. Click the **"🖨️ Print Label"** button
3. The print dialog will automatically open
4. Select your QL-820NWB printer
5. Print with 300 DPI settings

### Method 2: Manual Print
1. Generate label using web interface
2. Open the downloaded PNG file
3. Print using Brother QL Software
4. Select your QL-820NWB printer
5. Print with 300 DPI settings

### Method 2: Batch Printing (Recommended for Multiple Labels)
1. Go to the **"Batch Label Generation"** section
2. Enter multiple whisky IDs (comma-separated)
3. Select **"Brother QL-820NWB (Thermal)"** from Printer Type
4. Choose your preferred label size
5. Click **"🖨️ Generate & Print Batch"** button
6. Labels will be generated and print dialogs will open automatically
7. Each label will print with a 2-second delay between prints

### Method 3: Manual Batch Printing
1. Use the batch generation feature
2. Download the ZIP file with multiple labels
3. Print each label individually or use batch print software

### Method 3: API Integration
1. Use the API endpoints in your own applications
2. Automate label generation for large collections
3. Integrate with inventory management systems

## 🔧 Troubleshooting

### Common Issues:

**Labels too small/large:**
- Check label size preset in web interface
- Verify printer label size settings
- Use custom size for specific dimensions

**Poor print quality:**
- Ensure 300 DPI is selected
- Clean printer head
- Use genuine Brother QL labels
- Check label alignment

**QR codes not scanning:**
- QR codes are optimized for thermal printing
- Test with multiple QR scanner apps
- Ensure good lighting when scanning

**Text not readable:**
- Labels use pure black text for maximum contrast
- Check printer darkness settings
- Clean printer head if text appears faded

## 📊 Label Content

Each QL-820NWB optimized label includes:

1. **QR Code** (35% of label height)
   - Links to WhiskyBase page
   - Medium error correction for thermal printing
   - Centered at top of label

2. **Whisky Name** (Large font)
   - Centered, bold text
   - Truncated if too long

3. **Distillery** (Medium font)
   - "Distillery: [Name]" format
   - Centered text

4. **ABV** (Medium font)
   - "ABV: [Percentage]" format
   - Centered text

5. **Age** (Medium font, if available)
   - "Age: [Years]" format
   - Centered text

6. **Whisky ID** (Small font)
   - "ID: [Number]" format
   - Centered at bottom

## 🎯 Best Practices

1. **Use appropriate label size** for your bottles
2. **Test print** before large batches
3. **Store labels** in a cool, dry place
4. **Clean printer** regularly for best results
5. **Use genuine labels** for optimal adhesion

## 🔗 Integration Examples

### Python Script Example:
```python
import requests

# Generate QL-820NWB label
response = requests.get(
    'http://localhost:5000/api/ql820nwb/12345',
    params={'size': 'medium'}
)

# Save label
with open('whisky_label.png', 'wb') as f:
    f.write(response.content)
```

### JavaScript Example:
```javascript
// Generate QL-820NWB label
fetch('/api/ql820nwb/12345?size=medium')
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'whisky_label.png';
        a.click();
    });

// Generate and print batch labels
const batchData = {
    whisky_ids: [1, 123, 2, 10],
    printer_type: 'ql820nwb',
    ql820nwb_size: 'medium',
    width_mm: 29,
    height_mm: 90,
    dpi: 300
};

fetch('/api/batch-labels', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(batchData)
})
.then(response => response.blob())
.then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'batch_labels.zip';
    a.click();
});
```

## 📞 Support

If you encounter issues with QL-820NWB printing:

1. Check this guide for troubleshooting steps
2. Verify printer settings and connections
3. Test with different label sizes
4. Ensure you're using the QL-820NWB optimized endpoints

The QL-820NWB integration provides professional-quality thermal labels perfect for whisky collections!
