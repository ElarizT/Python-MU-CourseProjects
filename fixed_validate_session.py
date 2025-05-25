# Helper: Validate session state and handle refresh if needed
def validate_session():
    """
    Validates the current session and handles any issues.
    Returns True if the session is valid, False otherwise.
    """
    # Log detailed session state for debugging
    print(f"[SESSION VALIDATE] Session keys: {list(session.keys())}")
    print(f"[SESSION VALIDATE] User ID: {session.get('user_id', 'None')}")
    
    # First check if user_id exists and is not empty
    if 'user_id' not in session or not session.get('user_id'):
        print(f"[SESSION VALIDATE] No valid user_id in session")
        return False
        
    # Check for session age (optional security feature)
    current_time = time.time()
    login_time = session.get('login_time', 0)
    
    # Force re-login after 30 days (2592000 seconds) of inactivity
    if current_time - login_time > 2592000:
        print(f"[SESSION VALIDATE] Session too old, clearing")
        session.clear()
        return False
    
    # Check if the user still exists in Firebase (optional verification)
    try:
        uid = session.get('user_id')
        if uid:
            # Only verify with Firebase occasionally to reduce load
            # Increased verification frequency to 25% during debug
            should_verify = random.random() < 0.25  # 25% chance to verify while debugging
            
            if should_verify:
                try:
                    from firebase_admin import auth
                    auth.get_user(uid)  # Will raise exception if user doesn't exist
                    
                    # Update the login time after verification
                    session['login_time'] = current_time
                    session.modified = True
                    print(f"[SESSION VALIDATE] Firebase verification successful for {uid}")
                except Exception as firebase_error:
                    print(f"[SESSION VALIDATE] Firebase verification failed for {uid}: {firebase_error}")
                    session.clear()
                    return False
    except Exception as e:
        print(f"[SESSION VALIDATE] Session validation error: {e}")
        session.clear()
        return False
        
    # Update the login time if we're near the threshold
    if current_time - login_time > 3600:  # Update every hour
        print(f"[SESSION VALIDATE] Updating login time, old: {login_time}, new: {current_time}")
        session['login_time'] = current_time
        session.modified = True
        # Double check that the update was applied
        print(f"[SESSION VALIDATE] Verified updated login time: {session.get('login_time')}")
        
    print(f"[SESSION VALIDATE] Session is valid")
    return True
