#!/usr/bin/env python3
"""
Test script to verify the persistent session data fix is working.
This simulates the issue where 'azeri_text.txt' persists in session data.
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_FILE_NAME = "azeri_text.txt"

def test_session_persistence_fix():
    """Test that session clearing works properly and removes persistent data."""
    print(f"[{datetime.now()}] Starting persistent session data fix test...")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Make initial request to trigger @app.before_request
    print("\n1. Making initial request to trigger session clearing...")
    response = session.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    print(f"   Cookies: {dict(session.cookies)}")
    
    # Step 2: Simulate an upload that would create session data
    print("\n2. Simulating file upload to create session data...")
    # This simulates what would happen if we had persistent session data
    upload_data = {
        'action': 'test_upload',
        'filename': TEST_FILE_NAME,
        'content': 'Test content that should be cleared'
    }
    
    # Make a request to a route that would use session data
    response = session.get(f"{BASE_URL}/study")
    print(f"   Study page status: {response.status_code}")
    
    # Step 3: Make another request to see if session clearing triggers
    print("\n3. Making follow-up request to test session clearing...")
    response = session.get(f"{BASE_URL}/excel")
    print(f"   Excel page status: {response.status_code}")
    
    # Step 4: Test upload route specifically (which has session clearing)
    print("\n4. Testing upload route with session clearing...")
    response = session.get(f"{BASE_URL}/api/upload")
    print(f"   Upload API status: {response.status_code}")
    
    # Step 5: Test study upload route
    print("\n5. Testing study upload route...")
    response = session.get(f"{BASE_URL}/study/upload")
    print(f"   Study upload status: {response.status_code}")
    
    print(f"\n[{datetime.now()}] Test completed. Check Flask logs for session clearing messages.")
    print("Look for messages like '[STALE SESSION CLEANUP]' in the Flask console.")

def test_specific_azeri_detection():
    """Test the specific detection of azeri_text.txt in session data."""
    print(f"\n[{datetime.now()}] Testing specific azeri_text.txt detection...")
    
    session = requests.Session()
    
    # Make multiple requests to different routes to trigger before_request
    routes_to_test = [
        "/",
        "/study",
        "/excel", 
        "/presentation",
        "/proofread"
    ]
    
    for route in routes_to_test:
        print(f"\nTesting route: {route}")
        try:
            response = session.get(f"{BASE_URL}{route}")
            print(f"   Status: {response.status_code}")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("PERSISTENT SESSION DATA FIX TEST")
    print("=" * 60)
    
    try:
        test_session_persistence_fix()
        test_specific_azeri_detection()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY:")
        print("- Check the Flask console output for '[STALE SESSION CLEANUP]' messages")
        print("- Look for 'azeri_text.txt' detection and clearing messages")
        print("- Verify that session clearing functions are being called")
        print("=" * 60)
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
