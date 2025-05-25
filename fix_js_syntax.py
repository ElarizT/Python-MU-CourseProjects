"""
Script to fix JavaScript syntax issues in the website
"""
import os
import re
import shutil
from datetime import datetime

def create_backup(file_path):
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")

def fix_js_file(file_path):
    """Fix common JavaScript syntax errors"""
    # Skip if file doesn't exist
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return False
    
    # Create backup
    create_backup(file_path)
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    original_content = content
    
    # Fix 1: Missing closing parentheses in IIFE
    content = re.sub(
        r'\(function\(\) \{(.*?)\}\);?$',
        r'(function() {\1})();',
        content,
        flags=re.DOTALL
    )
    
    # Fix 2: Missing semicolons after statements
    content = re.sub(r'(\w+\(\))\s*$', r'\1;', content, flags=re.MULTILINE)
    
    # Fix 3: Ensure proper closure of function blocks
    content = re.sub(
        r'function ([a-zA-Z0-9_]+)\(\) \{(.*?)(?<!\})\s*\n(?=\s*function|\s*//|\s*$)',
        r'function \1() {\2\n}',
        content,
        flags=re.DOTALL
    )
    
    # Write the fixed content back only if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Fixed syntax issues in {file_path}")
        return True
    else:
        print(f"No changes needed for {file_path}")
        return False

def fix_all_js_files():
    """Fix syntax issues in all JavaScript files"""
    # Path to the js directory
    js_dir = r"c:\Users\taghi\.anaconda\static\js"
    
    # List of JavaScript files to check
    files_to_check = [
        os.path.join(js_dir, "ultimate-homepage-fix.js"),
        os.path.join(js_dir, "homepage-loading-fix.js"),
        os.path.join(js_dir, "landing-page.js"),
        os.path.join(js_dir, "loading-manager.js"),
        os.path.join(js_dir, "index-page.js"),
        os.path.join(js_dir, "index-page-loading-fix.js"),
        os.path.join(js_dir, "fix-loading-issue.js"),
    ]
    
    # Fix each file
    fixed_files = 0
    for file_path in files_to_check:
        if fix_js_file(file_path):
            fixed_files += 1
    
    print(f"Fixed {fixed_files} JavaScript files")

if __name__ == "__main__":
    fix_all_js_files()
