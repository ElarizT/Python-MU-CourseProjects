"""
Script to fix the image loading issue by creating a proper placeholder image
"""
import os
from pathlib import Path

# Base directory
base_dir = r'c:\Users\taghi\.anaconda'

# Image paths
placeholder_path = os.path.join(base_dir, 'static', 'images', 'feature-placeholder.jpg')

# Ensure the directory exists
Path(os.path.dirname(placeholder_path)).mkdir(parents=True, exist_ok=True)

print(f"Creating new placeholder image at: {placeholder_path}")

# Write a minimal HTML file that will serve as a placeholder instead
placeholder_html = os.path.join(base_dir, 'static', 'images', 'feature-placeholder.html')
with open(placeholder_html, 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html>
<head>
  <title>Image Placeholder</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 300px;
      background-color: #f0f0f0;
      font-family: Arial, sans-serif;
    }
    .placeholder {
      width: 100%;
      max-width: 400px;
      height: 300px;
      background-color: #e0e0e0;
      border: 1px dashed #aaa;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      color: #666;
    }
    .icon {
      font-size: 48px;
      margin-bottom: 10px;
    }
  </style>
</head>
<body>
  <div class="placeholder">
    <div class="icon">Image</div>
    <p>Image Placeholder</p>
  </div>
</body>
</html>
''')

# Create a very simple blank JPEG file for the placeholder
# This is much shorter and guaranteed to work
with open(placeholder_path, 'wb') as f:
    # A minimal valid JPEG file (1x1 pixel, white)
    jpeg_data = bytes([
        0xFF, 0xD8,                         # SOI marker
        0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x01, 0x00, 0x48, 0x00, 0x48, 0x00, 0x00,  # JFIF header
        0xFF, 0xDB, 0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12, 0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34, 0x32,  # DQT
        0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11, 0x00,  # SOF0 (baseline DCT)
        0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08,  # DHT
        0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # DHT
        0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0x37, 0xFF, 0xD9  # SOS and EOI
    ])
    f.write(jpeg_data)

size = os.path.getsize(placeholder_path)
print(f"Created new placeholder JPEG image ({size} bytes)")
print(f"Also created HTML placeholder: {placeholder_html}")

# Now update the onerror handler in all HTML files to handle errors better
import glob
import re

for html_file in glob.glob(os.path.join(base_dir, 'templates', '*.html')):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix any image tags with the problematic onerror handler
    updated_content = re.sub(
        r'<img([^>]*?)src="([^"]*?)"([^>]*?)onerror="this\.src=\'\/static\/images\/feature-placeholder\.jpg\'"([^>]*?)>',
        r'<img\1src="\2"\3onerror="if(this.src.indexOf(\'placeholder\')===-1){this.src=\'/static/images/feature-placeholder.jpg\';}else{this.onerror=null;this.src=\'/static/images/feature-placeholder.html\';}">\4',
        content
    )
    
    if updated_content != content:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Updated image error handling in: {html_file}")

print("Completed all fixes for the placeholder image issue")
