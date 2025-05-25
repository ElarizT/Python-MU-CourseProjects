"""
Script to verify and fix the layout.html file, ensuring there are no stray 
curly braces and that script tags are properly terminated.
"""
import os
import re
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    return backup_path

def fix_layout_html(file_path):
    """Fix syntax issues in layout.html"""
    # Create backup
    backup_file_path = backup_file(file_path)
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as file:
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
        
        if fixed_script != script_text:
            # Replace the script block
            content = content[:start_pos] + fixed_script + content[start_pos + len(script_text):]
            offset += len(fixed_script) - len(script_text)
    
    # Fix 3: Fix any malformed HTML tag structures
    # This is a basic fix - a full HTML parser would be better for complex cases
    content = re.sub(r'</div>\s*</div>\s*<div', '</div>\n                </div>\n                <div', content)

    # Check if anything was modified
    if content != original_content:
        # Write the changes back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Fixed syntax issues in {file_path}")
    else:
        print(f"No syntax issues found in {file_path}")
        
    print(f"Original file backed up at {backup_file_path}")

if __name__ == "__main__":
    layout_file = r'c:\Users\taghi\.anaconda\templates\layout.html'
    if os.path.exists(layout_file):
        fix_layout_html(layout_file)
    else:
        print(f"Error: Could not find {layout_file}")
