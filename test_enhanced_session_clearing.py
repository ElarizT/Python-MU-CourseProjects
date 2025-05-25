#!/usr/bin/env python3
"""
Test Enhanced Session Clearing

This script tests our enhanced session clearing functions including
the new aggressive_session_clear function.
"""

import sys
import os
from datetime import datetime

def test_enhanced_session_clearing():
    """Test the enhanced session clearing functions"""
    print("🔧 TESTING ENHANCED SESSION CLEARING")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now()}")
    print()
    
    # Mock Flask session with persistent data
    class MockPersistentSession(dict):
        def __init__(self):
            super().__init__()
            self.modified = False
            self.permanent = False
            # Simulate old persistent data like what's showing up in logs
            self['current_file'] = {
                'filename': 'azeri_text.txt',
                'file_id': 'old_file_id_123',
                'content': 'Old content that should be cleared...',
                'upload_time': '2025-05-20 10:30:00'
            }
            # Add some additional file-related keys that might persist
            self['file_metadata'] = {'last_upload': 'azeri_text.txt'}
            self['upload_status'] = 'completed'
            self['current_upload'] = 'azeri_text.txt'
    
    try:
        from file_optimizer import clear_flask_session_data, clear_all_session_data, aggressive_session_clear
        
        print("1️⃣ Testing enhanced clear_flask_session_data()...")
        session1 = MockPersistentSession()
        print(f"   Before: current_file = {session1.get('current_file', {}).get('filename', 'None')}")
        print(f"   Session keys before: {list(session1.keys())}")
        
        result1 = clear_flask_session_data(session1)
        print(f"   Result: {result1}")
        print(f"   After: current_file = {session1.get('current_file', {}).get('filename', 'None')}")
        print(f"   Session keys after: {list(session1.keys())}")
        print(f"   Modified: {session1.modified}, Permanent: {session1.permanent}")
        
        print("\n2️⃣ Testing aggressive_session_clear()...")
        session2 = MockPersistentSession()
        print(f"   Before: session keys = {list(session2.keys())}")
        
        result2 = aggressive_session_clear(session2)
        print(f"   Result: {result2}")
        print(f"   After: session keys = {list(session2.keys())}")
        
        # Check if all file-related data is gone
        file_keys = [k for k in session2.keys() if 'file' in k.lower() or 'upload' in k.lower()]
        if not file_keys:
            print("   ✅ All file-related data successfully cleared")
        else:
            print(f"   ❌ File-related keys still present: {file_keys}")
            
        print("\n3️⃣ Testing upload route integration...")
        # Simulate what happens in upload routes
        session3 = MockPersistentSession()
        print(f"   Simulating upload route with old data: {session3['current_file']['filename']}")
        
        # First aggressive clear
        aggressive_result = aggressive_session_clear(session3)
        print(f"   Aggressive clear result: {aggressive_result.get('status')}")
        
        # Then standard clear
        standard_result = clear_all_session_data(session3)
        print(f"   Standard clear result: {standard_result.get('status')}")
        
        # Check final state
        final_file_keys = [k for k in session3.keys() if 'file' in k.lower()]
        if not final_file_keys:
            print("   ✅ Upload route simulation: All file data cleared")
        else:
            print(f"   ❌ Upload route simulation: File keys remain: {final_file_keys}")
            
        print("\n4️⃣ Checking app.py integration...")
        # Verify the routes are updated
        try:
            with open('app.py', 'r', encoding='utf-8') as f:
                content = f.read()
            
            aggressive_calls = content.count('aggressive_session_clear')
            clear_all_calls = content.count('clear_all_session_data')
            
            print(f"   aggressive_session_clear calls: {aggressive_calls}")
            print(f"   clear_all_session_data calls: {clear_all_calls}")
            
            if aggressive_calls >= 2:
                print("   ✅ Aggressive clearing integrated in upload routes")
            else:
                print("   ❌ Aggressive clearing not found in upload routes")
                
        except Exception as e:
            print(f"   ❌ Error checking app.py: {e}")
        
        print("\n" + "=" * 60)
        print("📊 ENHANCED SESSION CLEARING TEST SUMMARY")
        print("=" * 60)
        print("✅ Enhanced clear_flask_session_data function tested")
        print("✅ Aggressive session clearing function tested")  
        print("✅ Upload route integration tested")
        print("\n🎯 NEXT STEPS FOR PRODUCTION:")
        print("1. Deploy the enhanced clearing functions")
        print("2. Monitor render.com logs for improved session clearing")
        print("3. Test with actual file uploads")
        print("4. Remove aggressive clearing once issue is resolved")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    test_enhanced_session_clearing()
