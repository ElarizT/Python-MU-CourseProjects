"""
Quick Fix Script for app.py

This script directly fixes both the duplicate route and syntax error issues
in the app.py file for production deployment.
"""

import re
import sys
import os
import shutil

def fix_app_py():
    """Fix the app.py file for production deployment."""
    # Path to app.py
    app_py_path = 'app.py'
    
    # Create a backup
    backup_path = 'app.py.bak'
    shutil.copy2(app_py_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    try:
        # Read the file content
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
          # Fix 1: Fix the syntax error in logout route (missing line break)
        content = re.sub(
            r'(resp = redirect\(url_for\(\'index\'\)\))\s+(resp\.delete_cookie)',
            r'\1\n    \2',
            content
        )
        
        # Fix 2: Fix another syntax error in headers section (missing line break)
        content = re.sub(
            r'(response\.headers\[\'Expires\'\] = \'0\')\s+(response\.headers\[\'X-Firebase-Reset\'\])',
            r'\1\n    \2',
            content
        )
        
        # Fix 3: Remove the duplicate logout_cleanup route
        content = re.sub(
            r'@app\.route\(\'\/logout_cleanup\'\)\s+def logout_cleanup\(\):\s+"""Server-side logout handler.+?session\[\'explicitly_logged_out\'\] = True\s+session\.modified = True',
            '',
            content,
            flags=re.DOTALL
        )
        
        # Fix 3: Remove the remaining part of the duplicate route implementation
        content = re.sub(
            r'# Log the logout page request.+?return render_template\(\'logout\.html\'.+?\)',
            '',
            content,
            flags=re.DOTALL
        )
        
        # Fix 4: Add a note about the route location
        content = re.sub(
            r'(return response, 200)',
            r'\1\n\n# Note: /logout_cleanup route is defined elsewhere in this file',
            content
        )
        
        # Write the fixed content back to the file
        with open(app_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Successfully fixed app.py!")        print("Changes made:")
        print("1. Fixed syntax error in logout route (added missing line break)")
        print("2. Fixed syntax error in headers section (added missing line break)")
        print("3. Removed duplicate logout_cleanup route definition")
        print("4. Added clarifying comments")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Restoring backup...")
        shutil.copy2(backup_path, app_py_path)
        print("Backup restored. No changes were made.")
        return False
    
    return True

if __name__ == "__main__":
    print("App.py Quick Fix Script")
    print("======================")
    print("This script will fix both the duplicate route and syntax error issues in app.py")
    print()
    
    proceed = input("Do you want to proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    success = fix_app_py()
    
    if success:
        deploy = input("Do you want to commit and push these changes? (y/n): ")
        if deploy.lower() == 'y':
            try:
                os.system('git add app.py')
                os.system('git commit -m "Fix duplicate route and syntax error in app.py"')
                os.system('git push')
                print("Changes deployed!")
            except Exception as e:
                print(f"Error during deployment: {e}")
        else:
            print("Changes made but not deployed. Manually push when ready.")
    else:
        print("Fix failed. Please check the app.py file manually.")
