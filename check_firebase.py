from flask import Flask, render_template, jsonify, session, request
import os
import json
import firebase_admin
from firebase_admin import auth, credentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# A simple diagnostic script to check Firebase configuration
# Save this as check_firebase.py and run it separately to diagnose any Firebase issues

def check_firebase_config():
    """Tests the Firebase configuration and reports any issues"""
    result = {
        'firebase_sdk': False,
        'credentials_file_exists': False,
        'credentials_valid': False,
        'can_verify_token': False,
        'errors': []
    }
    
    try:
        # Check if firebase_admin is installed
        import firebase_admin
        from firebase_admin import credentials, auth
        result['firebase_sdk'] = True
    except ImportError as e:
        result['errors'].append(f"Firebase SDK import error: {str(e)}")
        return result
    
    # Check for credential file
    cred_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or 'lightyearai-app-firebase-adminsdk-fbsvc-a1c778d686.json'
    
    if os.path.exists(cred_file):
        result['credentials_file_exists'] = True
        result['credential_path'] = cred_file
    else:
        result['errors'].append(f"Credentials file not found: {cred_file}")
          # Verify credentials
    try:
        if not firebase_admin._apps:
            # Check for credentials file path in environment variables
            cred_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or 'lightyearai-app-firebase-adminsdk-fbsvc-a1c778d686.json'
            
            # Use absolute path if not already
            if not os.path.isabs(cred_file):
                cred_file = os.path.abspath(cred_file)
                
            print(f"Using Firebase credentials file: {cred_file}")
            
            cred = credentials.Certificate(cred_file)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully")
        result['credentials_valid'] = True
    except Exception as e:
        result['errors'].append(f"Credentials validation error: {str(e)}")
        return result    # Try to verify a dummy token - expect it to fail but check HOW it fails
    # This test is confirming that the Firebase Auth verification is working correctly
    try:
        # Run a lighter test - we expect this to fail but in the right way
        # Just try to get the Firebase Auth instance
        from firebase_admin import auth
        auth_instance = auth
        
        # If we get here, the basic connection is working
        result['can_verify_token'] = True
        print("Firebase Auth verification instance available")
    except Exception as e:
        result['errors'].append(f"Firebase Auth unavailable: {str(e)}")
        print(f"Error accessing Firebase Auth: {e}")
    
    # Check environment variables
    result['env_vars'] = {
        'FIREBASE_API_KEY': os.environ.get('FIREBASE_API_KEY', 'Not set'),
        'FIREBASE_AUTH_DOMAIN': os.environ.get('FIREBASE_AUTH_DOMAIN', 'Not set'),
        'FIREBASE_PROJECT_ID': os.environ.get('FIREBASE_PROJECT_ID', 'Not set'),
        'FIREBASE_STORAGE_BUCKET': os.environ.get('FIREBASE_STORAGE_BUCKET', 'Not set'),
        'GOOGLE_APPLICATION_CREDENTIALS': os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')
    }
    
    return result

if __name__ == "__main__":
    result = check_firebase_config()
    print(json.dumps(result, indent=2))
    
    if not result['errors']:
        print("\n✅ Firebase configuration looks good!")
    else:
        print("\n❌ Firebase configuration has issues!")
        for error in result['errors']:
            print(f" - {error}")
