"""
Script to comprehensively fix layout.html JavaScript syntax issues
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
    """Fix JavaScript syntax issues in layout.html"""
    # Create backup
    create_backup(file_path)
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        
    # Fix escaped single quotes in JavaScript
    content = re.sub(r"getElementById\(\\+'global-loading-overlay\\+'\)", "getElementById('global-loading-overlay')", content)
    content = re.sub(r"style\.opacity = \\+'0\\+'", "style.opacity = '0'", content)
    content = re.sub(r"style\.display = \\+'none\\+'", "style.display = 'none'", content)
    
    # Fix indentation in JavaScript blocks
    def fix_js_indentation(match):
        js_block = match.group(1)
        lines = js_block.split('\n')
        indented_lines = []
        
        for line in lines:
            if line.strip():
                # Ensure there's proper indentation (4 spaces)
                stripped = line.lstrip()
                indented_line = '    ' + stripped
                indented_lines.append(indented_line)
            else:
                indented_lines.append(line)
                
        return '<script>\n' + '\n'.join(indented_lines) + '\n</script>'
    
    content = re.sub(r'<script>\s*(.*?)\s*</script>', fix_js_indentation, content, flags=re.DOTALL)
    
    # Fix missing braces in if blocks
    content = re.sub(
        r'if \(([^{]+?)\) \{\s+([^{}]+?)\s+return;\s*(?=\n)', 
        r'if (\1) {\n        \2\n        return;\n    }', 
        content,
        flags=re.DOTALL
    )
    
    # Fix broken IIFE closing
    content = re.sub(
        r'}\s*\)\(\);?\s*</script>', 
        r'})();\n</script>', 
        content
    )
    
    # Fix console.log lines not properly indented
    content = re.sub(
        r'console\.log\(\'([^\']+)\'\);', 
        r'    console.log(\'\1\');', 
        content
    )
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"Fixed JavaScript syntax issues in {file_path}")

if __name__ == "__main__":
    layout_html_path = r"c:\Users\taghi\.anaconda\templates\layout.html"
    fix_layout_html(layout_html_path)
