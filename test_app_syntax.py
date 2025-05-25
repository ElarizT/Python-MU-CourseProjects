"""
Test script to verify the app.py syntax is valid.
This script checks for syntax errors without actually running the app.
"""

import os
import py_compile
import sys

def test_app_syntax():
    """Test that app.py has valid syntax without importing it."""
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    
    try:
        # Just check if the syntax is valid by compiling the file
        # This won't execute the code, just check the syntax
        py_compile.compile(app_path, doraise=True)
        print("✓ SUCCESS: app.py has valid syntax!")
        return True
    except SyntaxError as e:
        print(f"✗ SYNTAX ERROR: {e}")
        print(f"  File: {e.filename}, Line {e.lineno}")
        print(f"  {e.text}")
        print(f"  {' ' * e.offset}^")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing app.py syntax...")
    success = test_app_syntax()
    if success:
        print("\nThe app.py file has valid syntax.")
        print("Both syntax errors have been fixed:")
        print("1. Line ~4465: Added line break after redirect call")
        print("2. Line ~4740: Added line break after setting Expires header")
        print("\nNote: This test only checks syntax correctness. It does not")
        print("check for other issues like duplicate routes.")
    else:
        print("\nThe app.py file still has syntax issues that need to be fixed.")
        print("Please check the error message above for details.")
