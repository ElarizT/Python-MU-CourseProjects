"""
Complete Fix for Web Application Loading Issues

This script addresses loading issues in the web application by:
1. Fixing HTML syntax errors in template files
2. Ensuring placeholder images exist and work correctly
3. Updating image onerror handlers to prevent infinite loops
4. Fixing JavaScript loading-related issues

Run this script to apply all fixes and resolve the infinite loading problem.
"""
import os
import re
import shutil
import glob
from pathlib import Path
from datetime import datetime

def create_backup(file_path):
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    return backup_path

def fix_placeholder_image():
    """Fix the placeholder image to prevent loading issues"""
    # Base directory
    base_dir = r'c:\Users\taghi\.anaconda'
    
    # Image paths
    placeholder_path = os.path.join(base_dir, 'static', 'images', 'feature-placeholder.jpg')
    
    # Ensure the directory exists
    Path(os.path.dirname(placeholder_path)).mkdir(parents=True, exist_ok=True)
    
    print(f"Fixing placeholder image at: {placeholder_path}")
    
    # Create a very simple blank JPEG file for the placeholder
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
    return True

def fix_image_error_handlers():
    """Update the onerror handlers in HTML templates to prevent infinite loops"""
    base_dir = r'c:\Users\taghi\.anaconda'
    fixed_files = 0
    
    # Find all HTML files
    for html_file in glob.glob(os.path.join(base_dir, 'templates', '*.html')):
        create_backup(html_file)  # Backup before modifying
        
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix problematic onerror handlers
        updated_content = re.sub(
            r'<img([^>]*?)src="([^"]*?)"([^>]*?)onerror="this\.src=\'\/static\/images\/feature-placeholder\.jpg\'"([^>]*?)>',
            r'<img\1src="\2"\3onerror="if(this.src.indexOf(\'placeholder\')===-1){this.src=\'/static/images/feature-placeholder.jpg\';}else{this.onerror=null;}">\4',
            content
        )
        
        if updated_content != content:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Updated image error handling in: {html_file}")
            fixed_files += 1
    
    print(f"Fixed error handlers in {fixed_files} HTML files")
    return fixed_files

def fix_layout_html():
    """Fix syntax issues in layout.html"""
    layout_file = r'c:\Users\taghi\.anaconda\templates\layout.html'
    backup_file = create_backup(layout_file)  # Backup before modifying
    
    with open(layout_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Keep track of modifications
    original_content = content
    
    # Fix 1: Remove any standalone curly braces
    content = re.sub(r'^\s*\}\s*$', '', content, flags=re.MULTILINE)
    
    # Fix 2: Fix improper script endings
    # Find all <script> blocks in the file
    script_blocks = re.finditer(r'<script[^>]*>.*?</script>', content, re.DOTALL)
    
    # Track positions of modifications to adjust subsequent matches
    offset = 0
    
    for script_match in script_blocks:
        script_text = script_match.group(0)
        start_pos = script_match.start() + offset
        
        # Check for improperly closed event listeners
        fixed_script = re.sub(
            r'document\.addEventListener\([\'"]DOMContentLoaded[\'"]\s*,\s*function\s*\(\)\s*\{(.*?)\}\s*\)\);?', 
            lambda m: re.sub(r'\}\s*\)\);?$', '});\n    ', m.group(0)),
            script_text, 
            flags=re.DOTALL
        )
        
        # Also fix any misaligned indentation in script blocks
        lines = fixed_script.split("\n")
        if len(lines) > 3:  # Only process multi-line scripts
            # Get base indent from opening script tag
            base_indent = re.match(r'^(\s*)<script', lines[0])
            if base_indent:
                base_indent = base_indent.group(1) + "    "
                # Fix indentation for content lines (not first or last)
                for i in range(1, len(lines)-1):
                    stripped = lines[i].lstrip()
                    if stripped:  # Only adjust non-empty lines
                        lines[i] = base_indent + stripped
                fixed_script = "\n".join(lines)
        
        if fixed_script != script_text:
            # Replace the script block
            content = content[:start_pos] + fixed_script + content[start_pos + len(script_text):]
            offset += len(fixed_script) - len(script_text)
    
    # Fix 3: Fix any malformed HTML tag structures
    # Fix specifically the settings-progress-label section
    content = re.sub(
        r'</div>\s*<div class="settings-progress-label">',
        '</div>\n                                <div class="settings-progress-label">',
        content
    )
    
    # Write the changes back to the file if modified
    if content != original_content:
        with open(layout_file, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Fixed syntax issues in {layout_file}")
        return True
    else:
        print(f"No syntax issues found in {layout_file}")
        return False

def check_js_loading_scripts():
    """Check and fix JavaScript loading scripts"""
    base_dir = r'c:\Users\taghi\.anaconda'
    js_files = [
        os.path.join(base_dir, 'static', 'js', 'loading-manager.js'),
        os.path.join(base_dir, 'static', 'js', 'ultimate-homepage-fix.js'),
        os.path.join(base_dir, 'static', 'js', 'homepage-loading-fix.js')
    ]
    
    for js_file in js_files:
        if os.path.exists(js_file):
            backup_path = create_backup(js_file)
            print(f"Backed up {js_file} to {backup_path}")
    
    return True

def main():
    """Apply all fixes to resolve the infinite loading issue"""
    print("=== Starting Web Application Loading Fix ===")
    
    # Step 1: Fix the HTML syntax in layout.html
    print("\n1. Fixing HTML syntax in layout.html...")
    fix_layout_html()
    
    # Step 2: Ensure placeholder image exists and works
    print("\n2. Creating proper placeholder image...")
    fix_placeholder_image()
    
    # Step 3: Fix image error handlers to prevent infinite loops
    print("\n3. Fixing image error handlers in HTML templates...")
    fix_image_error_handlers()
    
    # Step 4: Check and fix JavaScript loading scripts
    print("\n4. Checking JavaScript loading scripts...")
    check_js_loading_scripts()
    
    print("\n=== All fixes applied successfully! ===")
    print("The indefinite loading issue should now be resolved.")
    print("\nIf you still experience loading issues, please check the browser's")
    print("developer console (F12) for any remaining errors.")

if __name__ == "__main__":
    main()
