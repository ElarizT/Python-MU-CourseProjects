"""
Fix for Syntax Error in app.py Line 4740

This script directly fixes the syntax error at line 4740 in app.py
where there's a missing line break between response header assignments.
"""

import re
import sys
import os
import shutil

def fix_header_syntax_error():
    """Fix the syntax error in the header assignments at line 4740."""
    # Path to app.py
    app_py_path = 'app.py'
    
    # Create a backup
    backup_path = 'app.py.header.bak'
    shutil.copy2(app_py_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    try:
        # Read the file content
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the syntax error by adding a line break
        fixed_content = re.sub(
            r'(response\.headers\[\'Expires\'\] = \'0\')\s+(response\.headers\[\'X-Firebase-Reset\'\])',
            r'\1\n    \2',
            content
        )
        
        # Check if a change was made
        if fixed_content == content:
            print("Warning: No changes were made. The pattern might not match.")
            return False
        
        # Write the fixed content back to the file
        with open(app_py_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("Successfully fixed syntax error in app.py at line 4740!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Restoring backup...")
        shutil.copy2(backup_path, app_py_path)
        print("Backup restored. No changes were made.")
        return False
    
    return True

if __name__ == "__main__":
    print("App.py Header Syntax Error Fix Script")
    print("===================================")
    print("This script will fix the syntax error in app.py at line 4740")
    print("where there is a missing line break between response header assignments.")
    print()
    
    proceed = input("Do you want to proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    success = fix_header_syntax_error()
    
    if success:
        deploy = input("Do you want to commit and push this fix? (y/n): ")
        if deploy.lower() == 'y':
            try:
                os.system('git add app.py')
                os.system('git commit -m "Fix syntax error in app.py line 4740"')
                os.system('git push')
                print("Fix deployed!")
            except Exception as e:
                print(f"Error during deployment: {e}")
        else:
            print("Fix applied but not deployed. Manually push when ready.")
    else:
        print("Fix failed. Please check the app.py file manually.")
