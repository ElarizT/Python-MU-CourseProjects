"""
Firebase Authentication Diagnostic Tool

This script provides a comprehensive analysis of Firebase auth state
to help diagnose auth persistence issues.
"""

import json
import webbrowser
import time
import os
import sys
import requests
from urllib.parse import urlencode

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if your app runs on a different port

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 50)
    print(f" {title}")
    print("=" * 50)

def print_step(step, description):
    """Print a step in the diagnostic process"""
    print(f"\n[{step}] {description}")

def main():
    """Main diagnostic function"""
    clear_screen()
    print_section("FIREBASE AUTHENTICATION DIAGNOSTIC TOOL")
    print("\nThis tool will help diagnose Firebase authentication persistence issues")
    print("by analyzing the application's auth state and logout functionality.")
    
    # Menu of diagnostic options
    while True:
        print_section("DIAGNOSTIC OPTIONS")
        print("1. Open Auth Diagnostics Page")
        print("2. Test Regular Logout")
        print("3. Test Enhanced Logout")
        print("4. Check Firebase Auth Cache")
        print("5. Test Force Logout Script")
        print("6. Run Complete Diagnostic Flow")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ")
        
        if choice == "1":
            # Open Auth Diagnostics Page
            print_step(1, "Opening Auth Diagnostics Page")
            auth_diag_url = f"{BASE_URL}/auth-diagnostics?t={int(time.time())}"
            webbrowser.open(auth_diag_url)
            print("\nAuth diagnostics page opened in your browser.")
            
        elif choice == "2":
            # Test Regular Logout
            print_step(2, "Testing Regular Logout")
            logout_url = f"{BASE_URL}/logout"
            print(f"Sending request to: {logout_url}")
            
            try:
                response = requests.get(logout_url, allow_redirects=False)
                print(f"\nStatus code: {response.status_code}")
                print(f"Headers: {json.dumps(dict(response.headers), indent=4)}")
                
                if 300 <= response.status_code < 400:
                    print(f"\nRedirect location: {response.headers.get('Location')}")
                    
                print("\nNow opening the browser to complete the logout process...")
                webbrowser.open(logout_url)
            except Exception as e:
                print(f"\nError during logout request: {e}")
                
        elif choice == "3":
            # Test Enhanced Logout
            print_step(3, "Testing Enhanced Logout")
            logout_clean_url = f"{BASE_URL}/logout_cleanup?t={int(time.time())}"
            print(f"Opening enhanced logout page: {logout_clean_url}")
            webbrowser.open(logout_clean_url)
            
        elif choice == "4":
            # Check Firebase Auth Cache
            print_step(4, "Checking Firebase Auth Cache")
            print("To check Firebase Auth cache, you need to:")
            print("1. Open your browser's developer tools (F12)")
            print("2. Go to the Application tab")
            print("3. Check Local Storage, Session Storage, and IndexedDB")
            print("\nOpening auth diagnostics page for you to check...")
            
            auth_diag_url = f"{BASE_URL}/auth-diagnostics?t={int(time.time())}"
            webbrowser.open(auth_diag_url)
            
        elif choice == "5":
            # Test Force Logout Script
            print_step(5, "Testing Force Logout Script")
            print("This will test if the force-logout.js script correctly clears auth state")
            
            # First, set the explicit logout flag
            print("\nSetting explicitly_logged_out flag...")
            script_url = f"{BASE_URL}/auth-diagnostics?set_logout_flag=true&t={int(time.time())}"
            webbrowser.open(script_url)
            
            # Wait a moment for the page to load
            time.sleep(3)
            
            # Then reload any page to trigger the force-logout script
            print("\nNow reloading the page to trigger force-logout.js...")
            webbrowser.open(f"{BASE_URL}/?t={int(time.time())}")
            
        elif choice == "6":
            # Run Complete Diagnostic Flow
            print_step(6, "Running Complete Diagnostic Flow")
            
            print("\nStep 1: Checking current auth state...")
            webbrowser.open(f"{BASE_URL}/auth-diagnostics?t={int(time.time())}")
            input("Press Enter after checking auth state...")
            
            print("\nStep 2: Testing regular logout...")
            webbrowser.open(f"{BASE_URL}/logout")
            input("Press Enter after the logout completes...")
            
            print("\nStep 3: Checking auth state after regular logout...")
            webbrowser.open(f"{BASE_URL}/auth-diagnostics?t={int(time.time())}")
            input("Press Enter after checking post-logout auth state...")
            
            print("\nStep 4: Testing enhanced logout cleanup...")
            webbrowser.open(f"{BASE_URL}/logout_cleanup?t={int(time.time())}")
            input("Press Enter after the enhanced logout completes...")
            
            print("\nStep 5: Final auth state verification...")
            webbrowser.open(f"{BASE_URL}/auth-diagnostics?t={int(time.time())}")
            
            result = input("\nDid all logout tests clear the auth state properly? (yes/no): ")
            if result.lower() == "yes":
                print("\n✅ Success! Firebase logout functionality is working correctly.")
            else:
                print("\n❌ There are still issues with the logout functionality.")
                print("   Please check the diagnostic results for more details.")
            
        elif choice == "7":
            # Exit
            print("\nExiting Firebase Auth Diagnostic Tool...")
            sys.exit(0)
            
        else:
            print("\nInvalid choice. Please enter a number from 1 to 7.")
        
        input("\nPress Enter to continue...")
        clear_screen()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostic tool interrupted. Exiting...")
        sys.exit(0)
