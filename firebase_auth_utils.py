from flask import jsonify, session, redirect, url_for
from firebase_admin import auth
import firebase_admin
import time
import traceback

def check_firebase_initialized():
    """Check if Firebase is properly initialized"""
    if not firebase_admin._apps:
        print("ERROR: Firebase Admin SDK is not initialized!")
        return False
    return True

def handle_google_authentication(id_token, referral_code=None):
    """
    Handles Google Authentication in a consistent way across the application.
    
    Args:
        id_token (str): The Firebase ID token to verify
        referral_code (str, optional): A referral code if the user was referred
        
    Returns:
        tuple: (response_json, status_code)
    """
    # First check if Firebase is properly initialized
    if not check_firebase_initialized():
        return jsonify({
            'error': 'Authentication service unavailable. The server is not properly configured.',
            'redirect': url_for('auth_error', type='service_unavailable', 
                               message='The authentication service is currently unavailable (Firebase not initialized).')
        }), 503
    
    if not id_token:
        print("Error: No token provided in Google authentication request")
        return jsonify({'error': 'No token provided'}), 400
        
    try:
        # Print debug info
        print(f"Verifying Google authentication token (length: {len(id_token)})")
        
        # Verify the ID token with Firebase - make sure it's a string, not bytes
        if isinstance(id_token, bytes):
            id_token = id_token.decode('utf-8')
            
        # Check for a valid token format (basic validation)
        if id_token.count('.') != 2:
            print("Invalid token format: does not contain exactly two '.' characters")
            return jsonify({'error': 'Invalid token format'}), 400
        
        # Add a timeout for token verification to prevent hanging
        start_time = time.time()
        
        try:
            print(f"About to verify token with auth.verify_id_token, token starts with: {id_token[:20]}...")
            print(f"Firebase apps initialized: {len(firebase_admin._apps)}")
            decoded_token = auth.verify_id_token(id_token, check_revoked=True)
            print(f"Token verification took {time.time() - start_time:.2f} seconds")
        except auth.RevokedIdTokenError:
            print("Token has been revoked")
            return jsonify({'error': 'Authentication token has been revoked. Please sign in again.'}), 401
        except auth.ExpiredIdTokenError:
            print("Token has expired")
            return jsonify({'error': 'Authentication token has expired. Please sign in again.'}), 401
        except auth.InvalidIdTokenError:
            print("Token is invalid")
            return jsonify({'error': 'Invalid authentication token. Please sign in again.'}), 401
        except Exception as token_error:
            print(f"Unexpected token verification error: {str(token_error)}")
            return jsonify({'error': 'Authentication failed. Please try again.'}), 400
            
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        email_verified = decoded_token.get('email_verified', False)
        name = decoded_token.get('name', '')
        picture = decoded_token.get('picture', '')
        
        print(f"Token decoded for email: {email}, verified: {email_verified}")
        
        if not email_verified:
            print(f"Email not verified for user: {email}")
            return jsonify({'error': 'Please verify your email before logging in.'}), 400

        # Check if this is a new user
        is_new_user = False
        try:
            user = auth.get_user(uid)
            print(f"Existing user found: {uid}, email: {email}")
        except auth.UserNotFoundError:
            print(f"New user detected: {uid}, email: {email}")
            # Create a new user record in Firestore
            try:
                from firebase_admin import firestore
                
                auth.update_user(uid, display_name=name, photo_url=picture)
                firestore.client().collection('users').document(uid).set({
                    'email': email,
                    'display_name': name,
                    'photo_url': picture,
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'plan': 'free'
                })
                is_new_user = True
                print("New user record created in Firestore")
            except Exception as user_create_error:
                print(f"Error creating new user record: {user_create_error}")
                return jsonify({'error': f'Failed to create user account: {str(user_create_error)}'}), 500
                
        # Set session data
        try:
            # Make session permanent but with a specified lifetime
            from datetime import timedelta
            session.permanent = True
            # Set session lifetime to 30 days (adjust as needed)
            session.permanent_session_lifetime = timedelta(days=30)
            
            # Set user data in session
            session['user_id'] = uid
            session['user_email'] = email
            session['user_name'] = name
            session['user_picture'] = picture
            session['login_time'] = time.time()
            print(f"Session data set for user: {uid}")
            
            # Force session to be saved
            session.modified = True
        except Exception as session_error:
            print(f"Error setting session data: {session_error}")
            return jsonify({'error': 'Failed to create session. Please try again.'}), 500

        # Handle referral tracking for new users
        if is_new_user and referral_code:
            try:
                from referral_utils import track_referral
                track_referral(referral_code, uid)
                print(f"Referral tracked: {referral_code} for user {uid}")
            except Exception as referral_error:
                # Don't fail the login if referral tracking fails
                print(f"Error tracking referral: {referral_error}")
            
        print(f"Google authentication successful for user: {uid}")
        return jsonify({'success': True, 'isNewUser': is_new_user}), 200    
    except ValueError as ve:
        # This typically happens when the token is invalid
        print(f"Google auth token validation error: {ve}")
        error_details = str(ve)
        return jsonify({'error': 'Invalid authentication token. Please try again.', 'details': error_details}), 400
    except Exception as e:
        # Log detailed error information for debugging
        print(f"Error in Google authentication: {e}")
        print(f"Error type: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Determine if this is a Firebase initialization issue
        if "Firebase app" in str(e) and "not initialized" in str(e):
            return jsonify({
                'error': 'Authentication service unavailable. Please try again later.',
                'redirect': url_for('auth_error', type='service_unavailable', 
                                   message='The authentication service is currently unavailable.')
            }), 503
            
        return jsonify({'error': str(e)}), 400

def create_user_with_email_password(email, password, display_name=None):
    """
    Creates a new user with email and password in Firebase
    
    Args:
        email (str): User's email
        password (str): User's password
        display_name (str, optional): User's display name
        
    Returns:
        tuple: (user_record, None) if successful, (None, error_message) if failed
    """
    try:
        # First check if Firebase is properly initialized
        if not check_firebase_initialized():
            return None, "Authentication service unavailable"
        
        # Create the user in Firebase Auth
        user_properties = {
            'email': email,
            'password': password,
            'email_verified': False
        }
        
        if display_name:
            user_properties['display_name'] = display_name
            
        user_record = auth.create_user(**user_properties)
        
        # Create user record in Firestore
        try:
            from firebase_admin import firestore
            
            firestore.client().collection('users').document(user_record.uid).set({
                'email': email,
                'display_name': display_name or '',
                'created_at': firestore.SERVER_TIMESTAMP,
                'plan': 'free',
                'email_verified': False
            })
            
        except Exception as db_error:
            print(f"Error creating user record in Firestore: {db_error}")
            # We don't fail the user creation if only the Firestore record fails
        
        # Send verification email
        # Note: We can't do this from server - it must be done from client
        
        return user_record, None
        
    except auth.EmailAlreadyExistsError:
        return None, "Email already in use"
    except auth.InvalidEmailError:
        return None, "Invalid email address"
    except auth.WeakPasswordError:
        return None, "Password is too weak"
    except Exception as e:
        print(f"Error creating user: {e}")
        return None, str(e)

def verify_id_token(id_token):
    """
    Verify Firebase ID token
    
    Args:
        id_token (str): Firebase ID token
        
    Returns:
        tuple: (decoded_token, None) if successful, (None, error_message) if failed
    """
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token, None
    except auth.ExpiredIdTokenError:
        return None, "Token expired. Please sign in again."
    except auth.RevokedIdTokenError:
        return None, "Token revoked. Please sign in again."
    except auth.InvalidIdTokenError:
        return None, "Invalid token. Please sign in again."
    except Exception as e:
        print(f"Token verification error: {e}")
        return None, str(e)

def revoke_user_tokens(user_id, token=None):
    """
    Revokes all refresh tokens for a user, ensuring they're properly logged out.
    If a token is provided, it will be used to get the user ID if user_id is not provided.
    
    Args:
        user_id (str): The Firebase user ID
        token (str, optional): A Firebase ID token that can be used to get the user ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not check_firebase_initialized():
        print("ERROR: Firebase Admin SDK is not initialized, cannot revoke tokens!")
        return False
    
    try:
        # If token is provided but user_id is not, get user_id from token
        if token and not user_id:
            try:
                decoded_token = auth.verify_id_token(token)
                user_id = decoded_token['uid']
                print(f"Successfully decoded token to get user ID: {user_id}")
            except Exception as token_error:
                print(f"Error decoding token: {token_error}")
                return False
        
        if not user_id:
            print("ERROR: No user ID provided for token revocation")
            return False
        
        # Get user details to log email for debugging
        try:
            user = auth.get_user(user_id)
            print(f"Revoking tokens for user: {user.email} (UID: {user_id})")
        except Exception as user_error:
            print(f"Could not get user info for {user_id}: {user_error}")
            # Continue anyway since we have the UID
        
        # Revoke all tokens for this user
        auth.revoke_refresh_tokens(user_id)
        print(f"Successfully revoked all refresh tokens for user {user_id}")
        
        # Set user custom claims to indicate revoked status
        try:
            current_claims = auth.get_user(user_id).custom_claims or {}
            current_claims['tokens_revoked_at'] = int(time.time())
            auth.set_custom_user_claims(user_id, current_claims)
            print(f"Set token revocation timestamp in user claims for {user_id}")
        except Exception as claims_error:
            print(f"Warning: Could not set revocation timestamp in claims: {claims_error}")
        
        return True
    except Exception as revoke_error:
        print(f"Error revoking tokens: {revoke_error}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        return False
