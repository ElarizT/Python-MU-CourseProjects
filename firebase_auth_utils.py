from flask import jsonify, session, redirect, url_for
from firebase_admin import auth
import firebase_admin
import time
import traceback

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
    if not firebase_admin._apps:
        print("ERROR: Firebase Admin SDK is not initialized!")
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
        if not id_token.count('.') == 2:
            print(f"Invalid token format: does not contain exactly two '.' characters")
            return jsonify({'error': 'Invalid token format'}), 400
              # Add a timeout for token verification to prevent hanging
        import time
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
                print(f"New user record created in Firestore")
            except Exception as user_create_error:
                print(f"Error creating new user record: {user_create_error}")
                return jsonify({'error': f'Failed to create user account: {str(user_create_error)}'}), 500        # Set session data
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
