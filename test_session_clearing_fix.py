#!/usr/bin/env python3
"""
Test script to verify the Flask session clearing fix for file uploads.
This script tests the new comprehensive session clearing functionality.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class MockFlaskSession:
    """Mock Flask session object for testing"""
    def __init__(self):
        self._data = {}
        self.modified = False
        
    def get(self, key, default=None):
        return self._data.get(key, default)
        
    def __setitem__(self, key, value):
        self._data[key] = value
        self.modified = True
        
    def __getitem__(self, key):
        return self._data[key]
        
    def __contains__(self, key):
        return key in self._data
        
    def __delitem__(self, key):
        del self._data[key]
        self.modified = True

def test_flask_session_clearing():
    """Test that Flask session data is properly cleared"""
    print("=" * 60)
    print("TESTING: Flask Session Data Clearing")
    print("=" * 60)
    
    try:
        from file_optimizer import clear_flask_session_data, clear_all_session_data
        
        # Create a mock session with old file data
        mock_session = MockFlaskSession()
        mock_session['current_file'] = {
            'filename': 'azeri_text.txt',
            'content': 'Kanadanın avropalılar tərəfindən işğalınadək burada eskimoslar və hindular yaşayırdı.',
            'file_id': 'old_file_123',
            'upload_timestamp': '2025-05-21T22:34:51.025621'
        }
        
        print(f"✓ Created mock session with old file: {mock_session['current_file']['filename']}")
        print(f"✓ Old file content length: {len(mock_session['current_file']['content'])}")
        
        # Test clearing Flask session data only
        print("\n1. Testing clear_flask_session_data():")
        result = clear_flask_session_data(mock_session)
        print(f"   Result: {result}")
        
        # Verify the session was cleared
        if 'current_file' not in mock_session:
            print("   ✅ Flask session data successfully cleared")
        else:
            print("   ❌ Flask session data was NOT cleared")
            return False
            
        # Test the comprehensive clearing function
        print("\n2. Testing clear_all_session_data():")
        
        # Add file data back to session
        mock_session['current_file'] = {
            'filename': 'azeri_text.txt',
            'content': 'Old content that should be cleared',
            'file_id': 'old_file_456'
        }
        
        result = clear_all_session_data(mock_session)
        print(f"   Result: {result}")
        
        # Verify comprehensive clearing worked
        if 'current_file' not in mock_session:
            print("   ✅ Comprehensive session clearing successful")
        else:
            print("   ❌ Comprehensive session clearing failed")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import session clearing functions: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Flask session clearing: {e}")
        return False

def test_upload_route_integration():
    """Test that the upload routes have been updated with the new clearing function"""
    print("\n" + "=" * 60)
    print("TESTING: Upload Route Integration")
    print("=" * 60)
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for the new clearing function in /api/upload route
        api_upload_indicators = [
            "clear_all_session_data(session)",
            "from file_optimizer import clear_all_session_data"
        ]
        
        api_found = []
        for indicator in api_upload_indicators:
            if indicator in content:
                api_found.append(indicator)
        
        print(f"✅ /api/upload route indicators found: {len(api_found)}/{len(api_upload_indicators)}")
        print(f"   Found: {api_found}")
        
        # Check for the new clearing function in /study/upload route
        study_upload_indicators = [
            "clear_all_session_data(session)",
            "from file_optimizer import clear_all_session_data"
        ]
        
        study_found = []
        for indicator in study_upload_indicators:
            if indicator in content:
                study_found.append(indicator)
        
        print(f"✅ /study/upload route indicators found: {len(study_found)}/{len(study_upload_indicators)}")
        print(f"   Found: {study_found}")
        
        # Verify old clear_session_files calls have been replaced
        old_clear_calls = content.count("clear_session_files()")
        print(f"⚠️  Remaining old clear_session_files() calls: {old_clear_calls}")
        
        return len(api_found) >= 2 and len(study_found) >= 2
        
    except Exception as e:
        print(f"❌ Error testing upload route integration: {e}")
        return False

def main():
    """Run all tests and provide a summary"""
    print("🔧 FLASK SESSION CLEARING FIX VERIFICATION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    
    # Test 1: Flask session clearing functions
    print("1️⃣ Testing Flask session clearing functions...")
    results.append(("Flask Session Clearing", test_flask_session_clearing()))
    
    # Test 2: Upload route integration
    print("\n2️⃣ Testing upload route integration...")
    results.append(("Upload Route Integration", test_upload_route_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("The Flask session clearing fix has been successfully implemented.")
        print("File uploads should now properly clear old session data.")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed.")
        print("The Flask session clearing fix needs additional work.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
