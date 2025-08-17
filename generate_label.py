#!/usr/bin/env python3
"""
Command-line whisky label generator
Usage: python generate_label.py <whisky_id> [output_filename]
"""

import sys
import os
from app import WhiskyLabelGenerator

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_label.py <whisky_id> [output_filename]")
        print("Example: python generate_label.py 12345 my_whisky_label.png")
        sys.exit(1)
    
    try:
        whisky_id = int(sys.argv[1])
    except ValueError:
        print("Error: Whisky ID must be a number")
        sys.exit(1)
    
    # Set output filename
    if len(sys.argv) > 2:
        output_filename = sys.argv[2]
    else:
        output_filename = f"whisky_{whisky_id}_label.png"
    
    # Initialize the label generator
    generator = WhiskyLabelGenerator()
    
    print(f"Fetching whisky data for ID: {whisky_id}")
    
    # Get whisky information
    whisky_info = generator.get_whisky_info(whisky_id)
    
    if 'error' in whisky_info:
        print(f"Error fetching whisky data: {whisky_info['error']}")
        sys.exit(1)
    
    print(f"Whisky: {whisky_info['name']}")
    print(f"Distillery: {whisky_info['distillery']}")
    print(f"Region: {whisky_info['region']}")
    if whisky_info['age']:
        print(f"Age: {whisky_info['age']}")
    
    # Generate the label
    print("Generating label...")
    label_img = generator.create_label(whisky_info)
    
    # Save the label
    label_img.save(output_filename)
    print(f"Label saved as: {output_filename}")
    print(f"QR code links to: {whisky_info['url']}")

if __name__ == "__main__":
    main()
