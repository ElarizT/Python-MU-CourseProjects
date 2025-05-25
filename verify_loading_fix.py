"""
Verify that all fixes have been properly applied and no issues remain
"""
import os
import re
import sys

def check_file_exists(filepath):
    """Check if a file exists and return its size"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {filepath} exists ({size} bytes)")
        return True
    else:
        print(f"❌ {filepath} is missing")
        return False

def check_html_syntax(filepath):
    """Basic check for HTML syntax issues"""
    if not os.path.exists(filepath):
        print(f"❌ {filepath} is missing")
        return False
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for lone curly braces
    lone_braces = re.findall(r'^\s*\}\s*$', content, re.MULTILINE)
    if lone_braces:
        print(f"❌ {filepath} contains {len(lone_braces)} lone curly braces")
        return False
    
    # Check for image tags with simple onerror handlers
    simple_onerror = re.findall(r'onerror="this\.src=\'\/static\/images\/feature-placeholder\.jpg\'"', content)
    if simple_onerror:
        print(f"❌ {filepath} contains {len(simple_onerror)} simple onerror handlers that can cause infinite loops")
        return False
    
    print(f"✅ {filepath} has no obvious syntax issues")
    return True

def main():
    """Run all verification checks"""
    base_dir = r'c:\Users\taghi\.anaconda'
    
    print("=== Verification of Loading Issue Fixes ===\n")
    
    # Check 1: Verify placeholder image exists
    placeholder_path = os.path.join(base_dir, 'static', 'images', 'feature-placeholder.jpg')
    placeholder_exists = check_file_exists(placeholder_path)
    
    # Check 2: Verify layout.html syntax
    layout_path = os.path.join(base_dir, 'templates', 'layout.html')
    layout_ok = check_html_syntax(layout_path)
    
    # Check 3: Verify index.html and index_fixed.html
    index_path = os.path.join(base_dir, 'templates', 'index.html')
    index_fixed_path = os.path.join(base_dir, 'templates', 'index_fixed.html')
    index_ok = check_html_syntax(index_path)
    index_fixed_ok = check_html_syntax(index_fixed_path) if os.path.exists(index_fixed_path) else True
    
    # Check 4: Verify loading JS scripts exist
    loading_manager_js = os.path.join(base_dir, 'static', 'js', 'loading-manager.js')
    ultimate_fix_js = os.path.join(base_dir, 'static', 'js', 'ultimate-homepage-fix.js')
    homepage_fix_js = os.path.join(base_dir, 'static', 'js', 'homepage-loading-fix.js')
    
    js_exists = (
        check_file_exists(loading_manager_js) and
        check_file_exists(ultimate_fix_js) and
        check_file_exists(homepage_fix_js)
    )
    
    # Summary
    print("\n=== Summary ===")
    all_ok = placeholder_exists and layout_ok and index_ok and index_fixed_ok and js_exists
    
    if all_ok:
        print("✅ All checks passed! The loading issue should be resolved.")
        print("   The web application should now load properly without indefinite loading.")
    else:
        print("❌ Some issues remain. Please fix the reported issues.")
        print("   Check the console output above for details.")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
