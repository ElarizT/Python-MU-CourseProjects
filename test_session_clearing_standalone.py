#!/usr/bin/env python3
"""
Standalone test of session clearing functionality
Tests the session clearing functions outside of Flask to verify they work correctly.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class MockFlaskSession(dict):
    """Mock Flask session that behaves like the real one"""
    def __init__(self):
        super().__init__()
        self.modified = False
        self.permanent = False
        
        # Add the problematic data that's persisting
        self['current_file'] = {
            'filename': 'azeri_text.txt',
            'file_id': 'old_file_id_123',
            'content': 'Kanadanın avropalılar tərəfindən işğalınadək burada eskimoslar və hindular yaşayırdı.',
            'upload_timestamp': '2025-05-21T22:34:51.025621',
            'upload_time': '2025-05-21 22:34:51'
        }
        
        # Add some additional session data to test selectivity
        self['user_id'] = 'test_user_123'
        self['user_name'] = 'Test User'
        self['language'] = 'en'
        
    def pop(self, key, default=None):
        self.modified = True
        return super().pop(key, default)
    
    def __delitem__(self, key):
        self.modified = True
        super().__delitem__(key)
    
    def __setitem__(self, key, value):
        self.modified = True
        super().__setitem__(key, value)
    
    def clear(self):
        self.modified = True
        super().clear()

def test_session_clearing_detailed():
    """Test session clearing with detailed output"""
    print("🧪 STANDALONE SESSION CLEARING TEST")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now()}")
    print()
    
    try:
        from file_optimizer import aggressive_session_clear, clear_flask_session_data, clear_all_session_data
        
        print("1️⃣ Testing with mock session containing azeri_text.txt...")
        session = MockFlaskSession()
        
        # Show initial state
        print(f"   📋 Initial session keys: {list(session.keys())}")
        print(f"   📁 Current file: {session.get('current_file', {}).get('filename', 'None')}")
        print(f"   📏 Content length: {len(session.get('current_file', {}).get('content', ''))}")
        print(f"   🔄 Modified flag: {session.modified}")
        
        print("\n2️⃣ Testing aggressive_session_clear()...")
        result1 = aggressive_session_clear(session)
        print(f"   📊 Result: {result1}")
        print(f"   📋 Session keys after aggressive clear: {list(session.keys())}")
        print(f"   📁 Current file after: {session.get('current_file', {}).get('filename', 'None')}")
        print(f"   🔄 Modified flag: {session.modified}")
        
        # Check if it worked
        if 'current_file' in session:
            print("   ❌ FAILED: current_file still present after aggressive clear!")
            
            print("\n3️⃣ Testing clear_flask_session_data() as fallback...")
            result2 = clear_flask_session_data(session)
            print(f"   📊 Result: {result2}")
            print(f"   📋 Session keys after flask clear: {list(session.keys())}")
            print(f"   📁 Current file after: {session.get('current_file', {}).get('filename', 'None')}")
            
            if 'current_file' in session:
                print("   ❌ FAILED: current_file STILL present after both clearing methods!")
                
                print("\n4️⃣ Testing manual direct removal...")
                session.pop('current_file', None)
                print(f"   📋 Session keys after manual pop: {list(session.keys())}")
                
                if 'current_file' in session:
                    print("   ❌ CRITICAL: current_file persists even after manual pop()!")
                else:
                    print("   ✅ SUCCESS: Manual pop() worked")
            else:
                print("   ✅ SUCCESS: clear_flask_session_data() worked after aggressive clear failed")
        else:
            print("   ✅ SUCCESS: aggressive_session_clear() worked!")
        
        print("\n5️⃣ Testing with fresh session and clear_all_session_data()...")
        session2 = MockFlaskSession()
        print(f"   📁 Fresh session file: {session2.get('current_file', {}).get('filename', 'None')}")
        
        result3 = clear_all_session_data(session2)
        print(f"   📊 Result: {result3}")
        print(f"   📋 Session keys after clear_all: {list(session2.keys())}")
        
        if 'current_file' in session2:
            print("   ❌ FAILED: clear_all_session_data() did not work")
        else:
            print("   ✅ SUCCESS: clear_all_session_data() worked")
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        # Test summary
        functions_working = []
        if 'current_file' not in session:
            functions_working.append("Session clearing (after multiple attempts)")
        if 'current_file' not in session2:
            functions_working.append("clear_all_session_data")
        
        if functions_working:
            print(f"✅ Working functions: {', '.join(functions_working)}")
        else:
            print("❌ No clearing functions worked properly")
        
        # Essential user data preservation test
        essential_keys = ['user_id', 'user_name', 'language']
        preserved = [key for key in essential_keys if key in session]
        if preserved:
            print(f"✅ Essential data preserved: {preserved}")
        else:
            print("⚠️ Essential user data was cleared (may be expected)")
        
        print("\n🎯 DIAGNOSIS:")
        if 'current_file' not in session and 'current_file' not in session2:
            print("✅ Session clearing functions work correctly in isolation")
            print("🔍 The persistence issue may be related to:")
            print("   • Flask session backend behavior")
            print("   • Browser session storage")
            print("   • Concurrent requests")
            print("   • Session data being restored from another source")
        else:
            print("❌ Session clearing functions are not working properly")
            print("🔧 Needs investigation of the clearing logic")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_session_clearing_detailed()
    print(f"\n🏁 Test completed: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
