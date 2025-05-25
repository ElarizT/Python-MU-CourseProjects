#!/usr/bin/env python3
"""
Quick verification script to run after Flask restart
"""

def verify_fix_after_restart():
    print("🔍 VERIFICATION COMMANDS FOR AFTER RESTART")
    print("=" * 50)
    
    print("1️⃣ Check that session clearing function works:")
    print("   python -c \"from file_optimizer import clear_session_files; print(clear_session_files())\"")
    
    print("\n2️⃣ Test upload simulation:")
    print("   python test_upload_fix.py")
    
    print("\n3️⃣ Run comprehensive tests:")
    print("   python test_file_caching_fix.py")
    
    print("\n4️⃣ After uploading a file, check session logs should show:")
    print("   ✅ storage_type: 'session'")
    print("   ✅ file_id: 'session_*'")
    print("   ❌ NO download_url with googleapis.com")
    print("   ❌ NO storage_path")
    
    print("\n🎯 SUCCESS CRITERIA:")
    print("   • All tests pass")
    print("   • Session data contains only current file")
    print("   • No Firebase Storage URLs in session")
    print("   • New uploads clear old data")

if __name__ == "__main__":
    verify_fix_after_restart()
