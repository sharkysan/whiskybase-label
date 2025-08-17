#!/usr/bin/env python3
"""
Demo script showing how to use the WhiskyLabelGenerator programmatically
"""

from app import WhiskyLabelGenerator
import os

def main():
    print("🥃 Whisky Label Generator Demo")
    print("=" * 40)
    
    # Initialize the generator
    generator = WhiskyLabelGenerator()
    
    # Example whisky IDs to test
    test_ids = [12345, 67890, 11111]
    
    for whisky_id in test_ids:
        print(f"\nTesting whisky ID: {whisky_id}")
        print("-" * 30)
        
        # Get whisky information
        whisky_info = generator.get_whisky_info(whisky_id)
        
        print(f"Name: {whisky_info['name']}")
        print(f"Distillery: {whisky_info['distillery']}")
        print(f"Region: {whisky_info['region']}")
        if whisky_info['age']:
            print(f"Age: {whisky_info['age']}")
        if 'note' in whisky_info:
            print(f"Note: {whisky_info['note']}")
        
        # Generate label
        label_img = generator.create_label(whisky_info)
        
        # Save the label
        filename = f"demo_whisky_{whisky_id}.png"
        label_img.save(filename)
        print(f"Label saved as: {filename}")
        
        # Generate QR code separately
        qr_img = generator.generate_qr_code(whisky_id, 200)
        qr_filename = f"qr_whisky_{whisky_id}.png"
        qr_img.save(qr_filename)
        print(f"QR code saved as: {qr_filename}")
    
    print(f"\nDemo completed! Generated {len(test_ids)} labels and QR codes.")
    print("Check the current directory for the generated files.")

if __name__ == "__main__":
    main()
