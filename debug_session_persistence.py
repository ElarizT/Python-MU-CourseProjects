#!/usr/bin/env python3
"""
Debug Session Persistence Issue

This script helps debug why old session data (like azeri_text.txt) 
persists even after implementing session clearing fixes.
"""

import sys
import os
from datetime import datetime

def test_session_clearing_comprehensive():
    """Test comprehensive session clearing with detailed debugging"""
    print("🔍 DEBUGGING SESSION PERSISTENCE ISSUE")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now()}")
    print()
    
    # Mock Flask session that simulates the persistence issue
    class MockPersistentSession(dict):
        def __init__(self):
            super().__init__()
            self.modified = False
            # Simulate old persistent data
            self['current_file'] = {
                'filename': 'azeri_text.txt',
                'file_id': 'old_file_id_123',
                'content': 'Old content that should be cleared...',
                'upload_time': '2025-05-20 10:30:00'
            }
            print(f"🔴 SIMULATED OLD SESSION DATA: {self['current_file']['filename']}")
    
    # Test our clearing function
    try:
        from file_optimizer import clear_flask_session_data, clear_all_session_data
        
        print("\n1️⃣ Testing clear_flask_session_data()...")
        session = MockPersistentSession()
        print(f"   Before clearing: {session.get('current_file', {}).get('filename', 'None')}")
        
        result = clear_flask_session_data(session)
        print(f"   Clear result: {result}")
        print(f"   After clearing: {session.get('current_file', {}).get('filename', 'None')}")
        print(f"   Session modified flag: {session.modified}")
        
        # Test if data is actually gone
        if 'current_file' not in session:
            print("   ✅ Session data successfully cleared")
        else:
            print("   ❌ Session data still present!")
            
        print("\n2️⃣ Testing clear_all_session_data()...")
        session2 = MockPersistentSession()
        print(f"   Before clearing: {session2.get('current_file', {}).get('filename', 'None')}")
        
        result2 = clear_all_session_data(session2)
        print(f"   Clear result: {result2}")
        print(f"   After clearing: {session2.get('current_file', {}).get('filename', 'None')}")
        
        if 'current_file' not in session2:
            print("   ✅ Comprehensive session data successfully cleared")
        else:
            print("   ❌ Session data still present after comprehensive clear!")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    
    print("\n3️⃣ Checking current app.py routes...")
    
    # Check if routes are properly using the session clearing
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for upload routes
        upload_routes = []
        if 'clear_all_session_data(session)' in content:
            print("   ✅ Found clear_all_session_data(session) calls in app.py")
            
            # Count occurrences
            count = content.count('clear_all_session_data(session)')
            print(f"   📊 Found {count} calls to clear_all_session_data(session)")
            
            # Check specific routes
            if '@app.route(\'/api/upload\'' in content:
                upload_routes.append('/api/upload')
            if '@app.route(\'/study/upload\'' in content:
                upload_routes.append('/study/upload')
                
            print(f"   📁 Upload routes found: {upload_routes}")
        else:
            print("   ❌ clear_all_session_data(session) NOT found in app.py")
            
    except FileNotFoundError:
        print("   ❌ app.py file not found")
    except Exception as e:
        print(f"   ❌ Error reading app.py: {e}")
    
    print("\n4️⃣ Potential persistence issues to check:")
    print("   • Browser cache/cookies")
    print("   • Multiple Flask session backends")
    print("   • Race conditions between requests")
    print("   • Session data not properly committing")
    print("   • Old session data in browser localStorage")
    
    print("\n🔧 RECOMMENDED DEBUGGING STEPS:")
    print("1. Add more verbose logging to upload routes")
    print("2. Clear browser cache and cookies completely")
    print("3. Test with incognito/private browsing mode")
    print("4. Add session.permanent = True to ensure persistence")
    print("5. Add explicit session.pop('current_file', None) calls")
    
    return True

if __name__ == "__main__":
    test_session_clearing_comprehensive()
