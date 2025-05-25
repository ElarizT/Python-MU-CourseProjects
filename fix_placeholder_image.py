"""
Script to fix the image loading issue by verifying and ensuring
the placeholder image is properly accessible
"""
import os
import shutil
from pathlib import Path

# Base directory
base_dir = r'c:\Users\taghi\.anaconda'

# Image paths
original_image_path = os.path.join(base_dir, 'static', 'images', 'feature-knowledge.jpg')
placeholder_path = os.path.join(base_dir, 'static', 'images', 'feature-placeholder.jpg')

# Ensure the directories exist
Path(os.path.dirname(placeholder_path)).mkdir(parents=True, exist_ok=True)

# Check if placeholder exists
if not os.path.exists(placeholder_path):
    print(f"Placeholder image does not exist at: {placeholder_path}")
    
    # If original image exists, copy it as placeholder
    if os.path.exists(original_image_path):
        print(f"Copying original image as placeholder")
        shutil.copy2(original_image_path, placeholder_path)
    else:
        # Create a simple placeholder image
        print(f"Creating empty placeholder image")
        with open(placeholder_path, 'wb') as f:
            # Write a minimal valid JPEG file
            # This is a tiny valid JPEG that will display as a small empty image
            f.write(bytes.fromhex('ffd8ffe000104a46494600010101004800480000ffdb00430001010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101ffc00011080001000103012200021101031101ffc4001500010100000000000000000000000000000010ffc4001a10000103000000000000000000000000000111213171ffda000c03010002110311003f00b200c80ffd9'))
else:
    print(f"Verified that placeholder image exists at: {placeholder_path}")
    
# Check image size - if too small or empty, replace it
if os.path.exists(placeholder_path):
    size = os.path.getsize(placeholder_path)
    if size < 100:  # Less than 100 bytes is suspiciously small
        print(f"Placeholder image exists but is very small ({size} bytes). Creating a new one.")
        with open(placeholder_path, 'wb') as f:
            # Write a minimal valid JPEG file
            f.write(bytes.fromhex('ffd8ffe000104a46494600010101004800480000ffdb00430001010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101ffc00011080001000103012200021101031101ffc4001500010100000000000000000000000000000010ffc4001a10000103000000000000000000000000000111213171ffda000c03010002110311003f00b200c80ffd9'))

print("Done checking and fixing placeholder image")
