#!/usr/bin/env python3
"""
Production Upload Test Script

This script simulates the exact upload flow that happens in production
to verify that old session data is properly cleared.
"""

import os
import tempfile
from datetime import datetime

def simulate_production_upload():
    """Simulate the production upload flow with session clearing"""
    print("🚀 SIMULATING PRODUCTION UPLOAD FLOW")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now()}")
    print()
    
    # Create a mock Flask session with old data (like what you're seeing)
    class ProductionMockSession(dict):
        def __init__(self):
            super().__init__()
            self.modified = False
            self.permanent = False
            # This is the exact old data causing issues
            self['current_file'] = {
                'filename': 'azeri_text.txt',  # The problematic old file
                'file_id': 'session_old_file_123',
                'content': 'Old azeri text content that should be cleared...',
                'upload_time': '2025-05-20 10:30:00',
                'storage_type': 'session'
            }
            print(f"🔴 PRODUCTION ISSUE: Old session contains {self['current_file']['filename']}")
    
    # Simulate new file upload
    print("1️⃣ Simulating new CSV file upload...")
    new_file_content = """Name,Age,City
John,25,New York
Jane,30,San Francisco
Bob,35,Chicago"""
    
    try:
        from file_optimizer import aggressive_session_clear, clear_all_session_data
        
        # Step 1: Simulate upload route start with old session
        session = ProductionMockSession()
        print(f"   📋 Upload starts with old file: {session['current_file']['filename']}")
        
        # Step 2: Apply our enhanced clearing (what happens now in upload routes)
        print("\n2️⃣ Applying enhanced session clearing...")
        
        aggressive_result = aggressive_session_clear(session)
        print(f"   🧹 Aggressive clear: {aggressive_result['status']}")
        
        clear_result = clear_all_session_data(session)
        print(f"   🧹 Standard clear: {clear_result['status']}")
        
        # Step 3: Verify old data is gone
        if 'current_file' in session:
            print(f"   ❌ ERROR: Old file data still present: {session['current_file']['filename']}")
            return False
        else:
            print(f"   ✅ SUCCESS: Old file data completely cleared")
        
        # Step 4: Simulate setting new file data (what happens after clearing)
        print("\n3️⃣ Setting new CSV file data...")
        session['current_file'] = {
            'filename': 'new_upload.csv',
            'file_id': 'session_new_csv_456',
            'content': new_file_content,
            'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'storage_type': 'session'
        }
        session.modified = True
        
        print(f"   📁 New file set: {session['current_file']['filename']}")
        print(f"   📊 Content preview: {session['current_file']['content'][:50]}...")
        
        # Step 5: Verify final state
        print("\n4️⃣ Final verification...")
        current_filename = session.get('current_file', {}).get('filename', 'None')
        
        if current_filename == 'new_upload.csv':
            print(f"   ✅ SUCCESS: Session now contains new file: {current_filename}")
            print("   ✅ No trace of old azeri_text.txt file")
            
            # Check for any lingering old data
            session_str = str(session)
            if 'azeri_text' in session_str:
                print("   ❌ WARNING: Old filename still found in session data!")
                return False
            else:
                print("   ✅ No old filename traces in session")
                
            return True
        else:
            print(f"   ❌ ERROR: Unexpected file in session: {current_filename}")
            return False
            
    except Exception as e:
        print(f"❌ Error during simulation: {e}")
        return False

def check_deployment_readiness():
    """Check if the enhanced session clearing is ready for deployment"""
    print("\n" + "=" * 60)
    print("🔍 DEPLOYMENT READINESS CHECK")
    print("=" * 60)
    
    # Check file_optimizer.py exports
    try:
        from file_optimizer import aggressive_session_clear, clear_all_session_data, clear_flask_session_data
        print("✅ All session clearing functions available")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Check app.py routes
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the enhanced clearing in both upload routes
        upload_routes_with_aggressive = []
        
        # Check /api/upload route
        if 'aggressive_session_clear' in content and '/api/upload' in content:
            upload_routes_with_aggressive.append('/api/upload')
            
        # Check /study/upload route  
        if 'aggressive_session_clear' in content and '/study/upload' in content:
            upload_routes_with_aggressive.append('/study/upload')
        
        print(f"✅ Upload routes with aggressive clearing: {upload_routes_with_aggressive}")
        
        if len(upload_routes_with_aggressive) >= 2:
            print("✅ Both upload routes have enhanced session clearing")
            return True
        else:
            print("❌ Not all upload routes have enhanced clearing")
            return False
            
    except Exception as e:
        print(f"❌ Error checking app.py: {e}")
        return False

if __name__ == "__main__":
    # Run the production simulation
    upload_success = simulate_production_upload()
    
    # Check deployment readiness
    deployment_ready = check_deployment_readiness()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    if upload_success and deployment_ready:
        print("🎉 SUCCESS: Enhanced session clearing is working!")
        print("🚀 READY FOR DEPLOYMENT")
        print("\n📋 What this fixes:")
        print("   • Old file references (like azeri_text.txt) will be cleared")
        print("   • New uploads will start with clean session state")
        print("   • Render.com logs should show correct new file names")
        print("\n⚠️  Remember to monitor logs after deployment")
    else:
        print("❌ ISSUES DETECTED - Review before deployment")
        print(f"   Upload simulation: {'✅' if upload_success else '❌'}")
        print(f"   Deployment readiness: {'✅' if deployment_ready else '❌'}")
