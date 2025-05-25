#!/usr/bin/env python3
"""
Advanced test to simulate the persistent azeri_text.txt session data issue.
This will actually create session data with the problematic file and test the clearing mechanism.
"""

import requests
import json
from datetime import datetime
import time

# Test configuration
BASE_URL = "http://localhost:5000"
PROBLEMATIC_FILE = "azeri_text.txt"

def create_session_with_persistent_data():
    """Create a session that simulates having persistent file data."""
    print(f"[{datetime.now()}] Creating session with persistent data simulation...")
    
    session = requests.Session()
    
    # Step 1: First, get a valid session
    print("\n1. Establishing initial session...")
    response = session.get(f"{BASE_URL}/")
    print(f"   Initial session status: {response.status_code}")
    print(f"   Session cookies: {dict(session.cookies)}")
    
    # Step 2: Try to trigger upload routes that have session clearing
    print("\n2. Testing POST to upload routes with file data...")
    
    # Create test file data that simulates the problematic file
    test_files = {
        'file': ('azeri_text.txt', 'Test content that should be cleared from session', 'text/plain')
    }
    
    # Test the study upload route
    try:
        print("   Testing study upload route...")
        response = session.post(f"{BASE_URL}/study/upload", files=test_files)
        print(f"   Study upload status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Expected: Need authentication for upload")
    except Exception as e:
        print(f"   Study upload error: {e}")
    
    # Test the API upload route  
    try:
        print("   Testing API upload route...")
        response = session.post(f"{BASE_URL}/api/upload", files=test_files)
        print(f"   API upload status: {response.status_code}")
        if response.status_code == 401:
            print("   ✓ Expected: Need authentication for upload")
    except Exception as e:
        print(f"   API upload error: {e}")
        
    return session

def test_session_clearing_with_simulated_data():
    """Test session clearing when we have simulated persistent data."""
    print(f"\n[{datetime.now()}] Testing enhanced session clearing with simulated data...")
    
    # Create session with simulated data
    session = create_session_with_persistent_data()
    
    # Add a small delay to simulate time passing
    time.sleep(1)
    
    # Now make requests to routes to trigger the @app.before_request handler
    print("\n3. Making requests to trigger session clearing detection...")
    
    test_routes = [
        "/",           # Homepage
        "/study",      # Study page (should redirect to login)
        "/excel",      # Excel page (should redirect to login) 
        "/presentation", # Presentation page (should redirect to login)
    ]
    
    for route in test_routes:
        print(f"\n   Testing route: {route}")
        try:
            response = session.get(f"{BASE_URL}{route}")
            print(f"     Status: {response.status_code}")
            
            # Check if we got redirected to login (expected for protected routes)
            if response.history:
                print(f"     Redirected: {[r.status_code for r in response.history]} -> {response.url}")
            
        except Exception as e:
            print(f"     Error: {e}")
        
        # Small delay between requests
        time.sleep(0.5)

def check_session_clearing_logs():
    """Instructions for checking the session clearing logs."""
    print(f"\n[{datetime.now()}] CHECK SESSION CLEARING LOGS:")
    print("=" * 60)
    print("Look for these specific log messages in the Flask console:")
    print("1. '[STALE SESSION CLEANUP] IMMEDIATE CHECK: Found azeri_text.txt in session'")
    print("2. '[STALE SESSION CLEANUP] FORCE CLEARING: <filename> (<reason>)'")
    print("3. '[STALE SESSION CLEANUP] Session keys before clearing: [...]'")
    print("4. '[STALE SESSION CLEANUP] Aggressive clear result: {...}'")
    print("5. '[STALE SESSION CLEANUP] Session verification after clearing: [...]'")
    print("=" * 60)
    print("If you DON'T see these messages, it means:")
    print("- No persistent session data was detected (good!)")
    print("- The session clearing logic is not being triggered")
    print("- The issue may be in a different part of the system")

if __name__ == "__main__":
    print("=" * 70)
    print("ADVANCED PERSISTENT SESSION DATA TEST")
    print("=" * 70)
    
    try:
        # Run the comprehensive test
        test_session_clearing_with_simulated_data()
        
        # Show what to look for
        check_session_clearing_logs()
        
        print(f"\n[{datetime.now()}] Test completed.")
        print("\nTo manually create persistent session data:")
        print("1. Login to the application with a user account")
        print("2. Upload a file named 'azeri_text.txt'")
        print("3. Make requests to different routes")
        print("4. Look for the session clearing messages in Flask logs")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
