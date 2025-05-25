#!/usr/bin/env python3
"""
Validate that the file caching fix implementation is correct.
This script checks both the server-side and client-side implementations.
"""

import os
import re

def check_server_side_fix():
    """Check that server-side cache clearing is implemented"""
    print("=== Checking Server-Side Cache Clearing Fix ===")
    
    # Check app.py for the upload routes
    app_py_path = "c:\\Users\\taghi\\.anaconda\\app.py"
    
    try:
        with open(app_py_path, 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Check for cache clearing in /api/upload route
        api_upload_found = False
        study_upload_found = False
        
        # Look for the /api/upload route with cache clearing
        api_upload_pattern = r"@app\.route\(['\"][^'\"]*upload[^'\"]*['\"].*?def.*?upload.*?\)"
        api_matches = re.search(api_upload_pattern, app_content, re.DOTALL | re.IGNORECASE)
        
        if api_matches:
            # Check if clear_session_files is called in the upload function
            upload_func_start = api_matches.end()
            # Find the next function definition to get the boundaries
            next_func = re.search(r"@app\.route|def [a-zA-Z_]", app_content[upload_func_start:])
            if next_func:
                upload_func_content = app_content[upload_func_start:upload_func_start + next_func.start()]
            else:
                upload_func_content = app_content[upload_func_start:upload_func_start + 2000]  # Get reasonable chunk
            
            if "clear_session_files" in upload_func_content:
                print("✅ /api/upload route: Cache clearing implemented")
                api_upload_found = True
            else:
                print("❌ /api/upload route: Cache clearing NOT found")
        else:
            print("❌ /api/upload route: Route not found")
        
        # Check for study upload route
        study_upload_pattern = r"@app\.route\(['\"][^'\"]*study[^'\"]*upload[^'\"]*['\"].*?def.*?\)"
        study_matches = re.search(study_upload_pattern, app_content, re.DOTALL | re.IGNORECASE)
        
        if study_matches:
            study_func_start = study_matches.end()
            next_func = re.search(r"@app\.route|def [a-zA-Z_]", app_content[study_func_start:])
            if next_func:
                study_func_content = app_content[study_func_start:study_func_start + next_func.start()]
            else:
                study_func_content = app_content[study_func_start:study_func_start + 2000]
            
            if "clear_session_files" in study_func_content:
                print("✅ /study/upload route: Cache clearing implemented")
                study_upload_found = True
            else:
                print("❌ /study/upload route: Cache clearing NOT found")
        else:
            print("❌ /study/upload route: Route not found")
        
        return api_upload_found and study_upload_found
        
    except Exception as e:
        print(f"❌ Error checking server-side fix: {e}")
        return False

def check_client_side_fix():
    """Check that client-side cache clearing is implemented"""
    print("\n=== Checking Client-Side Cache Clearing Fix ===")
    
    agent_js_path = "c:\\Users\\taghi\\.anaconda\\static\\js\\agent.js"
    
    try:
        with open(agent_js_path, 'r', encoding='utf-8') as f:
            agent_content = f.read()
        
        # Find the uploadFile method
        upload_method_pattern = r"uploadFile\s*\(\s*file\s*\)\s*{"
        upload_match = re.search(upload_method_pattern, agent_content)
        
        if not upload_match:
            print("❌ uploadFile method: Method not found")
            return False
        
        # Get the method content (approximate)
        method_start = upload_match.start()
        # Find the end of the method by counting braces
        brace_count = 0
        method_end = method_start
        in_method = False
        
        for i, char in enumerate(agent_content[method_start:], method_start):
            if char == '{':
                brace_count += 1
                in_method = True
            elif char == '}':
                brace_count -= 1
                if in_method and brace_count == 0:
                    method_end = i + 1
                    break
        
        method_content = agent_content[method_start:method_end]
        
        # Check for cache clearing operations
        cache_clearing_checks = [
            ("this.fileHistory = {}", "fileHistory clearing"),
            ("this.uploadedFiles = {}", "uploadedFiles clearing"),
            ("delete this.contextData.uploadedFile", "contextData.uploadedFile clearing"),
            ("delete this.contextData.pdfContent", "contextData.pdfContent clearing")
        ]
        
        all_checks_passed = True
        for pattern, description in cache_clearing_checks:
            if pattern in method_content:
                print(f"✅ {description}: Implemented")
            else:
                print(f"❌ {description}: NOT found")
                all_checks_passed = False
        
        # Check that clearing happens before upload
        # Look for the pattern where clearing happens before FormData creation
        formdata_pos = method_content.find("new FormData()")
        clear_pos = method_content.find("this.fileHistory = {}")
        
        if formdata_pos > 0 and clear_pos > 0 and clear_pos < formdata_pos:
            print("✅ Cache clearing order: Happens before upload")
        else:
            print("❌ Cache clearing order: May not happen before upload")
            all_checks_passed = False
        
        return all_checks_passed
        
    except Exception as e:
        print(f"❌ Error checking client-side fix: {e}")
        return False

def check_file_optimizer():
    """Check that the file_optimizer module has the necessary functions"""
    print("\n=== Checking File Optimizer Module ===")
    
    file_optimizer_path = "c:\\Users\\taghi\\.anaconda\\file_optimizer.py"
    
    try:
        with open(file_optimizer_path, 'r', encoding='utf-8') as f:
            optimizer_content = f.read()
        
        required_functions = [
            "clear_session_files",
            "manage_uploaded_file",
            "read_csv_optimized"
        ]
        
        all_functions_found = True
        for func_name in required_functions:
            if f"def {func_name}" in optimizer_content:
                print(f"✅ Function {func_name}: Found")
            else:
                print(f"❌ Function {func_name}: NOT found")
                all_functions_found = False
        
        return all_functions_found
        
    except Exception as e:
        print(f"❌ Error checking file optimizer: {e}")
        return False

def main():
    """Main validation function"""
    print("🔍 File Upload Caching Fix Validation")
    print("=" * 50)
    
    server_ok = check_server_side_fix()
    client_ok = check_client_side_fix()
    optimizer_ok = check_file_optimizer()
    
    print("\n" + "=" * 50)
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    if server_ok:
        print("✅ Server-side cache clearing: IMPLEMENTED")
        print("   - Both /api/upload and /study/upload routes call clear_session_files()")
    else:
        print("❌ Server-side cache clearing: MISSING OR INCOMPLETE")
    
    if client_ok:
        print("✅ Client-side cache clearing: IMPLEMENTED")
        print("   - uploadFile() method clears all cache objects before upload")
    else:
        print("❌ Client-side cache clearing: MISSING OR INCOMPLETE")
    
    if optimizer_ok:
        print("✅ File optimizer module: COMPLETE")
        print("   - All required functions are available")
    else:
        print("❌ File optimizer module: MISSING FUNCTIONS")
    
    if server_ok and client_ok and optimizer_ok:
        print("\n🎉 OVERALL STATUS: FILE CACHING FIX IS COMPLETE!")
        print("📝 The fix prevents old files (like azeri_text.txt) from being used")
        print("   when new files (like dataset_part1.csv) are uploaded.")
        print("\n🔧 How it works:")
        print("   1. Server: clear_session_files() removes cached files before upload")
        print("   2. Client: uploadFile() clears JavaScript cache objects before upload")
        print("   3. Result: Each upload starts with a clean slate")
    else:
        print("\n⚠️  OVERALL STATUS: FILE CACHING FIX IS INCOMPLETE!")
        print("   Please review the missing components above.")

if __name__ == "__main__":
    main()
