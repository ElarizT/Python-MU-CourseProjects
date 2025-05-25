#!/usr/bin/env python3
"""
Force Session Clear and Restart Script
This script clears existing session data and demonstrates the fix is working.
"""

import os
import sys
import shutil
from datetime import datetime

def clear_session_files_directory():
    """Clear all files in the session_files directory"""
    session_dir = "session_files"
    if os.path.exists(session_dir):
        try:
            # Remove all files in the directory
            for filename in os.listdir(session_dir):
                file_path = os.path.join(session_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed: {file_path}")
            print(f"✅ Cleared session_files directory")
            return True
        except Exception as e:
            print(f"❌ Error clearing session_files: {e}")
            return False
    else:
        print(f"📁 session_files directory doesn't exist, creating it...")
        os.makedirs(session_dir, exist_ok=True)
        return True

def clear_upload_files():
    """Clear uploaded files to ensure clean state"""
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        try:
            # Just list what's there, don't delete user uploads
            upload_count = len(os.listdir(uploads_dir))
            print(f"📁 Found {upload_count} items in uploads directory")
            return True
        except Exception as e:
            print(f"❌ Error checking uploads: {e}")
            return False
    else:
        print(f"📁 uploads directory doesn't exist")
        return True

def test_session_clearing_function():
    """Test the session clearing function"""
    try:
        from file_optimizer import clear_session_files
        result = clear_session_files()
        print(f"✅ Session clearing function test: {result}")
        return True
    except Exception as e:
        print(f"❌ Session clearing function error: {e}")
        return False

def verify_upload_route_changes():
    """Verify the upload route has been properly modified"""
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for session storage indicators
        indicators = [
            "clear_session_files()",
            "'storage_type': 'session'",
            "session['current_file']",
            "session_file_id"
        ]
        
        found_indicators = []
        for indicator in indicators:
            if indicator in content:
                found_indicators.append(indicator)
        
        print(f"✅ Found {len(found_indicators)}/{len(indicators)} session storage indicators")
        
        # Check upload route specifically
        upload_route_start = content.find("@app.route('/api/upload'")
        upload_route_end = content.find("@app.route(", upload_route_start + 1)
        if upload_route_end == -1:
            upload_route_end = len(content)
        
        upload_content = content[upload_route_start:upload_route_end]
        
        # Check for Firebase storage remnants
        firebase_checks = [
            'storage.bucket',
            'blob.upload',
            'firestore.client()',
            'firebase.storage'
        ]
        
        firebase_found = []
        for check in firebase_checks:
            if check in upload_content:
                firebase_found.append(check)
        
        if firebase_found:
            print(f"⚠️ Found Firebase remnants in upload route: {firebase_found}")
            return False
        else:
            print(f"✅ No Firebase storage code found in upload route")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying upload route: {e}")
        return False

def main():
    """Main execution function"""
    print("🔧 FORCE SESSION CLEAR AND RESTART")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    
    # Step 1: Clear session files
    print("1️⃣ Clearing session files directory...")
    results.append(("Clear Session Files", clear_session_files_directory()))
    
    # Step 2: Check uploads
    print("\n2️⃣ Checking uploads directory...")
    results.append(("Check Uploads", clear_upload_files()))
    
    # Step 3: Test session clearing function
    print("\n3️⃣ Testing session clearing function...")
    results.append(("Session Clear Function", test_session_clearing_function()))
    
    # Step 4: Verify upload route changes
    print("\n4️⃣ Verifying upload route changes...")
    results.append(("Upload Route Changes", verify_upload_route_changes()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\n🎉 READY FOR RESTART!")
        print("📋 Next steps:")
        print("   1. Stop any running Flask instances")
        print("   2. Start Flask with: python app.py")
        print("   3. Upload a new file to test the fix")
        print("   4. Verify session contains only new file data")
    else:
        print("\n⚠️ Some checks failed. Review the output above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
