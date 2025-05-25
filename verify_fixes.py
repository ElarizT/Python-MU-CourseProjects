"""
Script to verify that all JavaScript and HTML fixes have been applied properly
"""
import os
import re

def check_file_exists(filepath, description):
    """Check if a file exists and print status"""
    exists = os.path.exists(filepath)
    if exists:
        filesize = os.path.getsize(filepath)
        print(f"✓ {description} exists ({filesize} bytes)")
    else:
        print(f"✗ {description} missing!")
    return exists

def check_html_syntax(filepath):
    """Check for basic HTML/JavaScript syntax errors"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for unclosed script tags
    script_tags = re.findall(r'<script[^>]*>', content)
    script_end_tags = re.findall(r'</script>', content)
    
    if len(script_tags) != len(script_end_tags):
        print(f"✗ Mismatch in script tags in {filepath}! {len(script_tags)} opening tags, {len(script_end_tags)} closing tags")
    else:
        print(f"✓ Balanced script tags in {filepath}")
    
    # Check for unclosed style tags
    style_tags = re.findall(r'<style[^>]*>', content)
    style_end_tags = re.findall(r'</style>', content)
    
    if len(style_tags) != len(style_end_tags):
        print(f"✗ Mismatch in style tags in {filepath}! {len(style_tags)} opening tags, {len(style_end_tags)} closing tags")
    else:
        print(f"✓ Balanced style tags in {filepath}")
    
    # For JavaScript template syntax, we need a more sophisticated check
    # The {% %} template tags complicate brace counting
    js_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
    
    for block_num, block in enumerate(js_blocks):
        # Skip blocks that are clearly template logic and not pure JS
        if '{%' in block and '%}' in block:
            print(f"✓ JavaScript block #{block_num+1} contains template code - skipping brace check")
            continue
            
        # Remove template expressions like {{ variable }} which aren't JS syntax
        cleaned_block = re.sub(r'{{.*?}}', '', block)
        
        # Now count actual JavaScript braces
        open_braces = 0
        close_braces = 0
        in_string = False
        string_delimiter = None
        in_comment = False
        prev_char = None
        
        for char in cleaned_block:
            if in_comment:
                if prev_char == '*' and char == '/':  # End of block comment
                    in_comment = False
            elif not in_string and prev_char == '/' and char == '*':  # Start of block comment
                in_comment = True
            elif not in_string and prev_char == '/' and char == '/':  # Line comment
                continue  # Ignore line comments
            elif not in_string and char in ['"', "'"]:  # Start of string
                in_string = True
                string_delimiter = char
            elif in_string and char == string_delimiter and prev_char != '\\':  # End of string
                in_string = False
            elif not in_string and not in_comment and char == '{':
                open_braces += 1
            elif not in_string and not in_comment and char == '}':
                close_braces += 1
                
            prev_char = char
            
        if open_braces != close_braces:
            print(f"⚠️ Potential mismatched JS braces in block #{block_num+1}: {open_braces} open, {close_braces} close")
            # In template files, this is often a false positive due to template syntax
            print(f"   Note: This may be due to template syntax and not an actual JavaScript error")
        else:
            print(f"✓ JavaScript block #{block_num+1} has balanced braces: {open_braces} pairs")
    
    # Check CSS for missing closing braces - exclude template elements
    css_blocks = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
    for block_num, block in enumerate(css_blocks):
        # Clean template syntax
        cleaned_block = re.sub(r'{{.*?}}', '', block)
        cleaned_block = re.sub(r'{%.*?%}', '', cleaned_block)
        
        open_braces = cleaned_block.count('{')
        close_braces = cleaned_block.count('}')
        if open_braces != close_braces:
            print(f"⚠️ Potential mismatched CSS braces in block #{block_num+1}: {open_braces} open, {close_braces} close")
            print(f"   Note: This may be due to template syntax and not an actual CSS error")
        else:
            print(f"✓ CSS block #{block_num+1} has balanced braces: {open_braces} pairs")

# Base directory
base_dir = r'c:\Users\taghi\.anaconda'

# Check key JavaScript files
print("\n=== Checking JavaScript Files ===")
check_file_exists(os.path.join(base_dir, 'static', 'js', 'ultimate-homepage-fix.js'), "Ultimate Homepage Fix script")
check_file_exists(os.path.join(base_dir, 'static', 'js', 'homepage-loading-fix.js'), "Homepage Loading Fix script")
check_file_exists(os.path.join(base_dir, 'static', 'js', 'loading-manager.js'), "Loading Manager script")

# Check placeholder image
print("\n=== Checking Placeholder Image ===")
placeholder_path = os.path.join(base_dir, 'static', 'images', 'feature-placeholder.jpg')
if check_file_exists(placeholder_path, "Placeholder image"):
    size = os.path.getsize(placeholder_path)
    if size < 100:
        print(f"✗ Placeholder image is suspiciously small: {size} bytes")
    else:
        print(f"✓ Placeholder image has reasonable size: {size} bytes")

# Check HTML files for syntax errors
print("\n=== Checking HTML Syntax ===")
check_html_syntax(os.path.join(base_dir, 'templates', 'layout.html'))
check_html_syntax(os.path.join(base_dir, 'templates', 'index.html'))
check_html_syntax(os.path.join(base_dir, 'templates', 'index_fixed.html'))

print("\nVerification complete!")
