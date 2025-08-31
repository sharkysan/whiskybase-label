#!/usr/bin/env python3
"""
Test script for QL-820NWB label generation
"""

from app import WhiskyLabelGenerator
import os

def test_ql820nwb_labels():
    """Test QL-820NWB label generation with different sizes"""
    print("🧪 Testing QL-820NWB Label Generation")
    print("=" * 50)
    
    # Initialize the generator
    generator = WhiskyLabelGenerator()
    
    # Test whisky data
    test_whisky = {
        'id': 12345,
        'name': 'Macallan 18 Year Old',
        'distillery': 'The Macallan',
        'abv': '43%',
        'age': '18 years',
        'url': 'https://www.whiskybase.com/whisky/12345',
        'source': 'test'
    }
    
    # Test different QL-820NWB sizes
    sizes = ['small', 'medium', 'large', 'custom']
    
    for size in sizes:
        print(f"\n📏 Testing {size.upper()} size...")
        
        try:
            # Generate QL-820NWB optimized label
            filename = generator.create_ql820nwb_label(test_whisky, f"test_ql820nwb_{size}.png", size_preset=size)
            
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"✅ Generated: {filename} ({file_size} bytes)")
            else:
                print(f"❌ Failed to generate: {filename}")
                
        except Exception as e:
            print(f"❌ Error generating {size} label: {e}")
    
    print(f"\n🎉 QL-820NWB test completed!")
    print("Check the current directory for generated test labels.")

if __name__ == "__main__":
    test_ql820nwb_labels()
