"""
This script verifies that all necessary image files for the website are present
and creates placeholders for any missing ones.
"""
import os
import shutil
from pathlib import Path

def create_minimal_jpeg(path, size=(1, 1)):
    """Create a minimal valid JPEG file at the specified path"""
    # This is a minimal valid JPEG that will display as a blank image
    with open(path, 'wb') as f:
        # Simple minimal JPEG hex data
        jpeg_hex = 'FFD8FFE000104A46494600010101000100010000FFDB004300080606070605080707070909080A0C140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C20242E2720222C231C1C2837292C30313434341F27393D38323C2E333432FFDB0043010909090C0B0C180D0D1832211C213232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232FFC00011080001000103012200021101031101FFC4001500010100000000000000000000000000000070FFC4001A10000103000000000000000000000000000102030A10FFC4001500010100000000000000000000000000000070FFC4001A10000103000000000000000000000000000102030A10FFDA000C03010002110311003F00BC000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007FFD9'
        f.write(bytes.fromhex(jpeg_hex))

def ensure_directory_exists(path):
    """Ensure that the directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)

def check_and_create_placeholders():
    """Check for and create placeholder images if needed"""
    print("Checking for required image files...")
    base_dir = r'c:\Users\taghi\.anaconda'
    
    # List of required image paths
    required_images = [
        os.path.join(base_dir, 'static', 'images', 'feature-knowledge.jpg'),
        os.path.join(base_dir, 'static', 'images', 'feature-placeholder.jpg'),
        os.path.join(base_dir, 'static', 'images', 'logo.png'),
        os.path.join(base_dir, 'static', 'images', 'hero-image.png'),
        os.path.join(base_dir, 'static', 'images', 'background.jpg'),
    ]
    
    # Check each required image
    for image_path in required_images:
        # Ensure the directory exists
        ensure_directory_exists(os.path.dirname(image_path))
        
        # Check if the image exists
        if not os.path.exists(image_path):
            print(f"Image does not exist: {image_path}")
            
            # Create a placeholder image
            if image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
                create_minimal_jpeg(image_path)
                print(f"Created placeholder JPEG: {image_path}")
            elif image_path.endswith('.png'):
                # For PNG, copy the placeholder image if it exists, otherwise create a blank JPEG
                placeholder_path = os.path.join(base_dir, 'static', 'images', 'feature-placeholder.jpg')
                if os.path.exists(placeholder_path):
                    shutil.copy2(placeholder_path, image_path)
                    print(f"Copied placeholder as: {image_path}")
                else:
                    create_minimal_jpeg(image_path)
                    print(f"Created placeholder image: {image_path}")
        else:
            print(f"Verified: {image_path}")

def verify_js_files():
    """Verify that all required JavaScript files exist"""
    print("Checking for required JavaScript files...")
    js_dir = r'c:\Users\taghi\.anaconda\static\js'
    
    # Ensure the directory exists
    ensure_directory_exists(js_dir)
    
    # List of required JavaScript files
    required_js = [
        'ultimate-homepage-fix.js',
        'homepage-loading-fix.js',
        'landing-page.js',
        'loading-manager.js',
        'index-page.js',
        'fix-loading-issue.js',
    ]
    
    # Check each required JavaScript file
    for js_file in required_js:
        file_path = os.path.join(js_dir, js_file)
        if os.path.exists(file_path):
            print(f"Verified: {file_path}")
        else:
            # Create a minimal JavaScript file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'/**\n * {js_file} - placeholder file\n * Created by verification script\n */\n\nconsole.log("{js_file} loaded");')
            print(f"Created placeholder JS file: {file_path}")

if __name__ == "__main__":
    # Check for required image files
    check_and_create_placeholders()
    
    # Verify JavaScript files
    verify_js_files()
    
    print("All required files have been verified and placeholders created as needed.")
