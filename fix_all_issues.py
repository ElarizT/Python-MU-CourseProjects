"""
Final fix for all website loading issues
"""
import os
import sys
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

def create_backup(file_path):
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")

def fix_placeholder_image():
    """Fix placeholder image issue"""
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
            create_minimal_jpeg(placeholder_path)
    else:
        print(f"Verified that placeholder image exists at: {placeholder_path}")
        
    # Check image size - if too small or empty, replace it
    if os.path.exists(placeholder_path):
        size = os.path.getsize(placeholder_path)
        if size < 100:  # Less than 100 bytes is suspiciously small
            print(f"Placeholder image exists but is very small ({size} bytes). Creating a new one.")
            create_minimal_jpeg(placeholder_path)

def create_minimal_jpeg(path):
    """Create a minimal valid JPEG file"""
    with open(path, 'wb') as f:
        jpeg_hex = 'FFD8FFE000104A46494600010101000100010000FFDB004300080606070605080707070909080A0C140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C20242E2720222C231C1C2837292C30313434341F27393D38323C2E333432FFDB0043010909090C0B0C180D0D1832211C213232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232FFC00011080001000103012200021101031101FFC4001500010100000000000000000000000000000070FFC4001A10000103000000000000000000000000000102030A10FFC4001500010100000000000000000000000000000070FFC4001A10000103000000000000000000000000000102030A10FFDA000C03010002110311003F00BC000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000007FFD9'
        f.write(bytes.fromhex(jpeg_hex))

def fix_js_files():
    """Fix JavaScript files"""
    # Directory containing JavaScript files
    js_dir = r'c:\Users\taghi\.anaconda\static\js'
    
    # JavaScript files to check and fix
    js_files = [
        'ultimate-homepage-fix.js',
        'homepage-loading-fix.js',
        'index-page.js',
        'fix-loading-issue.js',
        'loading-manager.js',
        'landing-page.js'
    ]
    
    for js_file in js_files:
        file_path = os.path.join(js_dir, js_file)
        if os.path.exists(file_path):
            print(f"Fixing {js_file}...")
            fix_js_file(file_path)
        else:
            print(f"Creating {js_file}...")
            create_js_file(js_file, file_path)

def fix_js_file(file_path):
    """Fix common JavaScript syntax errors in a file"""
    # Create backup
    create_backup(file_path)
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fix missing closing parenthesis in IIFEs
    content = re.sub(r'\}\s*\)\s*;?$', '})();', content, flags=re.MULTILINE)
    
    # Fix stray semicolons
    content = re.sub(r';\s*\)\s*;', ');', content)
    
    # Fix unclosed blocks
    def fix_unclosed_blocks(match):
        block = match.group(1)
        if block.count('{') > block.count('}'):
            # Add missing closing braces
            missing_braces = block.count('{') - block.count('}')
            return block + ('}' * missing_braces)
        return block
    
    # Apply block fixes
    content = re.sub(r'(function\s*\([^)]*\)\s*\{[^}]*(?:\{[^}]*\}[^}]*)*)', fix_unclosed_blocks, content)
    
    # Write the fixed content back
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Fixed {file_path}")

def create_js_file(js_name, file_path):
    """Create a basic JavaScript file"""
    content = f"""/**
 * {js_name} - Auto-created by fix script
 * 
 * This file was generated to fix 404 errors on the website.
 */

(function() {{
    'use strict';
    
    console.log('{js_name} loaded');
    
    // Only run on the homepage
    if (window.location.pathname === '/' || window.location.pathname === '') {{
        // Hide any loading screens
        const loadingOverlay = document.getElementById('global-loading-overlay');
        if (loadingOverlay) {{
            loadingOverlay.style.display = 'none';
            loadingOverlay.style.opacity = '0';
        }}
        
        // Use LoadingManager if available
        if (window.LoadingManager && typeof window.LoadingManager.hideLoading === 'function') {{
            window.LoadingManager.hideLoading();
        }}
    }}
}})();
"""
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write the content to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Created {file_path}")

def fix_layout_html():
    """Fix JavaScript syntax issues in layout.html"""
    file_path = r"c:\Users\taghi\.anaconda\templates\layout.html"
    
    # Create backup
    create_backup(file_path)
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fix 1: Replace any escaped single quotes
    content = content.replace("\\'", "'")
    
    # Fix 2: Fix indentation in JavaScript blocks
    def fix_indentation(match):
        script_content = match.group(1)
        lines = script_content.split('\n')
        indented_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped:
                indented_lines.append(f"    {stripped}")
            else:
                indented_lines.append("")
        
        return f"<script>\n{'\n'.join(indented_lines)}\n</script>"
    
    content = re.sub(r'<script>\s*(.*?)\s*</script>', fix_indentation, content, flags=re.DOTALL)
    
    # Fix 3: Fix IIFE syntax
    content = re.sub(
        r'\(function\(\) \{(.*?)\}\)\(\);?',
        r'(function() {\1})();',
        content,
        flags=re.DOTALL
    )
    
    # Fix 4: Fix missing closing braces
    # Count opening and closing braces in each script block
    def fix_braces(match):
        script_content = match.group(1)
        opening_braces = script_content.count('{')
        closing_braces = script_content.count('}')
        
        if opening_braces > closing_braces:
            # Add missing closing braces
            missing = opening_braces - closing_braces
            return f"<script>\n{script_content}{'}' * missing}\n</script>"
        
        return f"<script>\n{script_content}\n</script>"
    
    content = re.sub(r'<script>\s*(.*?)\s*</script>', fix_braces, content, flags=re.DOTALL)
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Fixed JavaScript syntax issues in {file_path}")

def fix_index_html():
    """Fix JavaScript syntax issues in index.html"""
    file_path = r"c:\Users\taghi\.anaconda\templates\index.html"
    
    # Create backup
    create_backup(file_path)
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fix 1: Fix broken style tag
    content = re.sub(
        r'document\.write\(\'<style id="homepage-loading-fix-style">(.*?)</style>\'\);(\s*)\/\/ PART 2',
        r'document.write(\'<style id="homepage-loading-fix-style">\1</style>\');\2\n        // PART 2',
        content,
        flags=re.DOTALL
    )
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Fixed JavaScript syntax issues in {file_path}")

def verify_js_files():
    """Verify that all required JavaScript files exist"""
    base_dir = r'c:\Users\taghi\.anaconda\static\js'
    required_files = [
        'ultimate-homepage-fix.js',
        'homepage-loading-fix.js',
        'index-page.js',
        'loading-manager.js',
        'landing-page.js',
        'fix-loading-issue.js',
    ]
    
    for file_name in required_files:
        file_path = os.path.join(base_dir, file_name)
        if not os.path.exists(file_path):
            print(f"Creating missing file: {file_name}")
            create_js_file(file_name, file_path)
        else:
            print(f"Verified file exists: {file_name}")

def run_fix_script():
    """Run all fixes"""
    print("Starting comprehensive fix script...")
    
    print("\n1. Fixing placeholder images...")
    fix_placeholder_image()
    
    print("\n2. Fixing JavaScript files...")
    fix_js_files()
    
    print("\n3. Fixing layout.html...")
    fix_layout_html()
    
    print("\n4. Fixing index.html...")
    fix_index_html()
    
    print("\n5. Verifying all required JS files...")
    verify_js_files()
    
    print("\nAll fixes complete!")

if __name__ == "__main__":
    run_fix_script()
