from dotenv import load_dotenv
import os
import base64
import tempfile
import firebase_admin
from firebase_admin import credentials, auth
import json

def test_firebase_credentials():
    # Load environment variables from .env
    print("Loading environment variables...")
    load_dotenv()
    
    # Try both methods of initialization
    # Method 1: Using GOOGLE_APPLICATION_CREDENTIALS
    print("\n--- Method 1: Using GOOGLE_APPLICATION_CREDENTIALS ---")
    cred_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    print(f"Credential file path: {cred_file}")
    print(f"File exists: {os.path.exists(cred_file) if cred_file else False}")
    
    # Method 2: Using FIREBASE_CREDENTIALS_BASE64
    print("\n--- Method 2: Using FIREBASE_CREDENTIALS_BASE64 ---")
    firebase_credentials_base64 = os.environ.get('FIREBASE_CREDENTIALS_BASE64')
    if firebase_credentials_base64:
        print(f"Base64 credentials: {firebase_credentials_base64[:30]}...{firebase_credentials_base64[-10:]}")
        
        # Decode the base64 string
        try:
            json_content = base64.b64decode(firebase_credentials_base64).decode('utf-8')
            cred_json = json.loads(json_content)
            print(f"Successfully decoded credentials JSON with keys: {list(cred_json.keys())}")
            print(f"Project ID from credentials: {cred_json.get('project_id')}")
            
            # Write to temp file and try to initialize
            temp_cred_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json')
            temp_cred_file.write(json_content)
            temp_cred_file.close()
            
            print(f"Wrote credentials to temporary file: {temp_cred_file.name}")
            
            # Reset Firebase apps
            for app in list(firebase_admin._apps.values()):
                app.delete()
                
            # Try to initialize with the temp file
            try:
                cred = credentials.Certificate(temp_cred_file.name)
                storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET', 'lightyearai-app.firebasestorage.app')
                
                firebase_admin.initialize_app(cred, {
                    'storageBucket': storage_bucket
                })
                print(f"Firebase initialized successfully with temporary credential file!")
                
                # Test auth
                print("Testing Auth API...")
                try:
                    # Just a simple API call to test connectivity
                    page = auth.list_users()
                    user_count = 0
                    # Just count first few users
                    for user in page.iterate_all():
                        user_count += 1
                        if user_count >= 3:
                            break
                    print(f"Auth API working! Found {user_count} users.")
                except Exception as auth_error:
                    print(f"Auth API test failed: {auth_error}")
                
            except Exception as init_error:
                print(f"Firebase initialization failed: {init_error}")
            
        except Exception as decode_error:
            print(f"Failed to decode base64 credentials: {decode_error}")
    else:
        print("No base64 credentials found in environment variables")
    
    print("\nTest complete!")

if __name__ == "__main__":
    test_firebase_credentials()
