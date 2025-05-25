"""
Syntax Error Fix Script for app.py

This script specifically fixes syntax errors in app.py where missing line breaks
are causing the application to fail in production.
"""

import re
import sys
import os
import shutil

def fix_syntax_error():
    """Fix syntax errors in app.py where missing line breaks are causing issues."""
    # Path to app.py
    app_py_path = 'app.py'
    
    # Create a backup
    backup_path = 'app.py.syntax.bak'
    shutil.copy2(app_py_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    try:
        # Read the file content
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        changes_made = 0
        
        # Fix 1: First syntax error by adding a line break (around line 4465)
        fixed_content = re.sub(
            r'(resp = redirect\(url_for\(\'index\'\)\))\s+(resp\.delete_cookie)',
            r'\1\n    \2',
            content
        )
        
        if fixed_content != content:
            changes_made += 1
            content = fixed_content
            print("Fixed syntax error #1: Added line break after redirect call")
        
        # Fix 2: Second syntax error by adding a line break (around line 4740)
        fixed_content = re.sub(
            r'(response\.headers\[\'Expires\'\] = \'0\')\s+(response\.headers\[\'X-Firebase-Reset\'\])',
            r'\1\n    \2',
            content
        )
        
        if fixed_content != content:
            changes_made += 1
            content = fixed_content
            print("Fixed syntax error #2: Added line break after Expires header")
        
        # Check if any changes were made
        if changes_made == 0:
            print("Warning: No changes were made. The patterns might not match.")
            return False
        
        # Write the fixed content back to the file
        with open(app_py_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"Successfully fixed {changes_made} syntax error(s) in app.py!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Restoring backup...")
        shutil.copy2(backup_path, app_py_path)
        print("Backup restored. No changes were made.")
        return False
    
    return True

if __name__ == "__main__":
    print("App.py Syntax Error Fix Script")
    print("=============================")
    print("This script will fix syntax errors in app.py")
    print("where missing line breaks are causing the app to fail.")
    print()
    
    proceed = input("Do you want to proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    success = fix_syntax_error()
    
    if success:
        deploy = input("Do you want to commit and push this fix? (y/n): ")
        if deploy.lower() == 'y':
            try:
                os.system('git add app.py')
                os.system('git commit -m "Fix syntax errors in app.py"')
                os.system('git push')
                print("Fix deployed!")
            except Exception as e:
                print(f"Error during deployment: {e}")
        else:
            print("Fix applied but not deployed. Manually push when ready.")
    else:
        print("Fix failed. Please check the app.py file manually.")
