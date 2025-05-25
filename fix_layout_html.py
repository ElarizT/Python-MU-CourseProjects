"""
Script to fix the syntax error in layout.html
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

def fix_layout_html(file_path):
    """Fix the syntax errors in layout.html"""
    # Create backup
    create_backup(file_path)
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Fix 1: Fix the script with DOMContentLoaded listener
    pattern1 = r'document\.addEventListener\(\'DOMContentLoaded\', function\(\) \{(.*?)\}\s*\)\);'
    replacement1 = lambda m: re.sub(r'\}\s*\)\);$', '});\n    ', m.group(0))
    content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
    
    # Fix 2: Fix any stray closing braces
    content = re.sub(r'^\s*\}\s*$', '', content, flags=re.MULTILINE)
    
    # Fix 3: Fix the HTML structure around settings-progress-label
    content = re.sub(
        r'</div>\s*<div class="settings-progress-label">',
        '</div>\n                                <div class="settings-progress-label">',
        content
    )
      # Fix 4: Fix broken return statements
    content = re.sub(
        r'return;\n\n\n',
        r'return;\n    }\n',
        content
    )
    
    # Fix 5: Fix broken function blocks
    content = re.sub(
        r'function hideLoadingNow\(\) \{\s+const overlay = document\.getElementById\(\'global-loading-overlay\'\);\s+if \(overlay\) \{\s+overlay\.style\.opacity = \'0\';\s+overlay\.style\.display = \'none\';\s*\n\n\n',
        r'function hideLoadingNow() {\n        const overlay = document.getElementById(\'global-loading-overlay\');\n        if (overlay) {\n            overlay.style.opacity = \'0\';\n            overlay.style.display = \'none\';\n        }\n    }\n\n    ',
        content
    )
    
    # Write the fixed content back
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Fixed syntax errors in {file_path}")

if __name__ == "__main__":
    layout_html_path = r"c:\Users\taghi\.anaconda\templates\layout.html"
    fix_layout_html(layout_html_path)
