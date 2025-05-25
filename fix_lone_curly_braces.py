"""
Fix lone curly braces in index.html and index_fixed.html
"""
import os
import re
from datetime import datetime
import shutil

def create_backup(file_path):
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    return backup_path

def fix_lone_curly_braces(file_path):
    """Remove lone curly braces"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
        
    create_backup(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix lone curly braces
    updated_content = re.sub(r'^\s*\}\s*$', '', content, flags=re.MULTILINE)
    
    if updated_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Fixed lone curly braces in {file_path}")
        return True
    else:
        print(f"No lone curly braces found in {file_path}")
        return True

# Fix the files
base_dir = r'c:\Users\taghi\.anaconda'
index_path = os.path.join(base_dir, 'templates', 'index.html')
index_fixed_path = os.path.join(base_dir, 'templates', 'index_fixed.html')

fix_lone_curly_braces(index_path)
fix_lone_curly_braces(index_fixed_path)
