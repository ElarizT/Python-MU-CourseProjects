"""
Script to specifically fix the stray curly brace in layout.html
"""
import re

# Path to the layout file
file_path = r'c:\Users\taghi\.anaconda\templates\layout.html'

# Read the content
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Look for any standalone curly braces on their own line and remove them
fixed_content = re.sub(r'^\s*\}\s*$', '', content, flags=re.MULTILINE)

# Write the fixed content back
with open(file_path, 'w', encoding='utf-8') as file:
    file.write(fixed_content)

print(f"Removed stray curly braces from {file_path}")

# Additional fix - check the script block with DOMContentLoaded
matches = re.findall(r'<script>.*?document\.addEventListener\(\'DOMContentLoaded\'.*?</script>', fixed_content, re.DOTALL)
if matches:
    print(f"Found {len(matches)} DOMContentLoaded script blocks to check.")
    
    # Check for any malformed script ending
    for i, match in enumerate(matches):
        if '})' in match and not '});' in match:
            print(f"Found potentially malformed script ending in block {i+1}")
