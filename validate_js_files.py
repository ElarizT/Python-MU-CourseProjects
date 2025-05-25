"""
Script to validate all JavaScript files for syntax errors
"""
import os
import re
import subprocess
import sys
import json
from pathlib import Path

# Node.js script to validate JavaScript syntax
VALIDATE_SCRIPT = """
const fs = require('fs');
const path = require('path');

// Get the file path from command line args
const filePath = process.argv[2];

try {
    // Try to parse the file
    const content = fs.readFileSync(filePath, 'utf8');
    
    try {
        // Use Function constructor to check syntax (safer than eval)
        new Function(content);
        console.log(JSON.stringify({ success: true, message: "File syntax is valid" }));
    } catch (syntaxError) {
        console.log(JSON.stringify({ success: false, message: syntaxError.message, line: syntaxError.lineNumber, column: syntaxError.columnNumber }));
    }
} catch (error) {
    console.log(JSON.stringify({ success: false, message: `Error reading file: ${error.message}` }));
}
"""

def has_node_js():
    """Check if Node.js is installed"""
    try:
        # Run 'node -v' command to check if Node.js is installed
        process = subprocess.run(['node', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.returncode == 0
    except FileNotFoundError:
        return False

def validate_js_file(file_path):
    """Validate a JavaScript file using Node.js"""
    if not has_node_js():
        print("Node.js is not installed or not in PATH. Cannot validate JavaScript syntax.")
        return False
        
    # Create a temporary validation script
    temp_dir = Path.cwd()
    script_path = temp_dir / "validate_js.js"
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(VALIDATE_SCRIPT)
    
    try:
        # Run the validation script
        process = subprocess.run(
            ['node', str(script_path), file_path], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        # Parse the output
        if process.returncode != 0:
            print(f"Error validating {file_path}: {process.stderr}")
            return False
            
        try:
            result = json.loads(process.stdout)
            if result['success']:
                print(f"✓ {file_path} - valid")
                return True
            else:
                print(f"✗ {file_path} - syntax error: {result['message']}")
                if 'line' in result and 'column' in result:
                    print(f"  at line {result['line']}, column {result['column']}")
                return False
        except json.JSONDecodeError:
            print(f"Error parsing validation result for {file_path}: {process.stdout}")
            return False
    finally:
        # Clean up the temporary script
        if script_path.exists():
            script_path.unlink()

def validate_js_files():
    """Validate all JavaScript files in the static/js directory"""
    base_dir = r"c:\Users\taghi\.anaconda"
    js_dir = os.path.join(base_dir, "static", "js")
    
    print(f"Validating JavaScript files in {js_dir}")
    
    valid_count = 0
    invalid_count = 0
    
    # Get all .js files
    for file_name in os.listdir(js_dir):
        if file_name.endswith('.js'):
            file_path = os.path.join(js_dir, file_name)
            
            if validate_js_file(file_path):
                valid_count += 1
            else:
                invalid_count += 1
    
    print(f"\nValidation complete: {valid_count} valid files, {invalid_count} invalid files")
    
    return invalid_count == 0

if __name__ == "__main__":
    if validate_js_files():
        print("All JavaScript files are valid!")
        sys.exit(0)
    else:
        print("Some JavaScript files have syntax errors!")
        sys.exit(1)
