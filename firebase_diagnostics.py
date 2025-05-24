from flask import Blueprint, jsonify
import os
import base64
import json
import tempfile
import firebase_admin
from firebase_admin import auth, credentials
import traceback

# Create a blueprint for Firebase diagnostic routes
firebase_diagnostics = Blueprint('firebase_diagnostics', __name__)

@firebase_diagnostics.route('/api/check-firebase-auth', methods=['GET'])
def check_firebase_auth():
    """Endpoint to specifically check Firebase authentication status"""
    response = {
        'firebase_initialized': len(firebase_admin._apps) > 0,
        'status': 'unknown',
        'environment_vars': {},
        'diagnostics': {},
        'auth_test': {'success': False, 'message': 'Not attempted'},
        'credential_test': {'success': False, 'message': 'Not attempted'}
    }
    
    # Check environment variables
    env_vars = [
        'FIREBASE_API_KEY', 
        'FIREBASE_AUTH_DOMAIN',
        'FIREBASE_DATABASE_URL',
        'FIREBASE_PROJECT_ID',
        'FIREBASE_STORAGE_BUCKET',
        'FIREBASE_MESSAGING_SENDER_ID',
        'FIREBASE_APP_ID',
        'FIREBASE_MEASUREMENT_ID',
        'GOOGLE_APPLICATION_CREDENTIALS',
        'FIREBASE_CREDENTIALS_BASE64'
    ]
    
    for var in env_vars:
        has_var = var in os.environ
        value = os.environ.get(var)
        if var == 'FIREBASE_CREDENTIALS_BASE64' and has_var and value:
            # Only show first and last few characters
            display_value = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "Invalid value"
            response['environment_vars'][var] = {'exists': True, 'value': display_value}
        else:
            response['environment_vars'][var] = {'exists': has_var, 'value': value if has_var and var != 'FIREBASE_API_KEY' else None}
    
    # Check if Firebase is initialized
    if len(firebase_admin._apps) > 0:
        response['status'] = 'initialized'
        
        # Try a simple Auth API call
        try:
            # Just list one user to test connection
            auth.list_users(max_results=1)
            response['auth_test'] = {'success': True, 'message': 'Successfully connected to Firebase Auth API'}
        except Exception as e:
            response['auth_test'] = {
                'success': False, 
                'message': f'Error connecting to Firebase Auth API: {str(e)}',
                'traceback': traceback.format_exc()
            }
    else:
        response['status'] = 'not_initialized'
        
        # Try to initialize Firebase using credentials from environment
        firebase_credentials_base64 = os.environ.get('FIREBASE_CREDENTIALS_BASE64')
        if firebase_credentials_base64:
            try:
                # Decode base64 string
                json_content = base64.b64decode(firebase_credentials_base64).decode('utf-8')
                cred_json = json.loads(json_content)
                
                response['credential_test'] = {
                    'success': True,
                    'message': f"Successfully decoded credentials for project: {cred_json.get('project_id')}",
                    'project_id': cred_json.get('project_id')
                }
                
                # Don't actually initialize Firebase here to avoid conflicts
            except Exception as e:
                response['credential_test'] = {
                    'success': False,
                    'message': f'Error decoding credentials: {str(e)}',
                    'traceback': traceback.format_exc()
                }
                
    return jsonify(response)

# Function to register the blueprint with the Flask app
def register_firebase_diagnostics(app):
    app.register_blueprint(firebase_diagnostics)
