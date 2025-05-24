# Chat history utilities for Firebase

from firebase_admin import firestore
import firebase_utils
import time
import json
from datetime import datetime

def get_user_chats(user_id, limit=20):
    """
    Get all chat sessions for a user.
    
    Args:
        user_id (str): User ID
        limit (int): Maximum number of chats to retrieve
    
    Returns:
        list: List of chat sessions
    """
    if not user_id:
        print("Cannot get chat sessions: No user ID provided")
        return []
    
    try:
        db = firestore.client()
        
        # Query the chats collection for this user
        chats_ref = (db.collection('users')
                     .document(user_id)
                     .collection('chat_sessions')
                     .order_by('timestamp', direction=firestore.Query.DESCENDING)
                     .limit(limit))
        
        chats = []
        for doc in chats_ref.stream():
            chat_data = doc.to_dict()
            # Add the document ID as chat ID if not present
            if 'id' not in chat_data:
                chat_data['id'] = doc.id

            # Normalize timestamp to ISO string
            timestamp = chat_data.get('timestamp')
            if not isinstance(timestamp, str):
                try:
                    # Firestore Timestamp has to_datetime()
                    if hasattr(timestamp, 'to_datetime'):
                        dt = timestamp.to_datetime()
                    # Fallback to seconds/nanos
                    elif hasattr(timestamp, 'seconds'):
                        dt = datetime.fromtimestamp(timestamp.seconds + (timestamp.nanos / 1e9))
                    # Already a datetime
                    elif isinstance(timestamp, datetime):
                        dt = timestamp
                    else:
                        raise TypeError
                    chat_data['timestamp'] = dt.isoformat()
                except Exception:
                    chat_data['timestamp'] = str(timestamp)
             
            chats.append(chat_data)
            
        return chats
    
    except Exception as e:
        print(f"Error getting user chats: {e}")
        return []

def save_chat_session(user_id, chat_data):
    """
    Save a chat session to Firestore.

    Args:
        user_id (str): User ID
        chat_data (dict): Chat session data
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not user_id:
        print("Cannot save chat session: No user ID provided")
        return False
    
    try:
        db = firestore.client()
        
        # Use the provided chat ID as the document ID
        chat_id = chat_data.get('id')
        if not chat_id:
            print("Cannot save chat session: No chat ID provided")
            return False
        
        # Create a copy of chat_data to avoid modifying the original
        chat_to_save = chat_data.copy()
        
        # Always set timestamp on server for consistency across devices
        chat_to_save['timestamp'] = firestore.SERVER_TIMESTAMP
        
        # Save to user's chat_sessions collection
        chat_ref = (db.collection('users')
                    .document(user_id)
                    .collection('chat_sessions')
                    .document(chat_id))
        
        chat_ref.set(chat_to_save, merge=True)
        return True
    
    except Exception as e:
        print(f"Error saving chat session: {e}")
        return False

def delete_chat_session(user_id, chat_id):
    """
    Delete a chat session from Firestore.
    
    Args:
        user_id (str): User ID
        chat_id (str): Chat session ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not user_id or not chat_id:
        print("Cannot delete chat session: Missing user ID or chat ID")
        return False
    
    try:
        db = firestore.client()
        
        # Delete the chat document
        chat_ref = (db.collection('users')
                    .document(user_id)
                    .collection('chat_sessions')
                    .document(chat_id))
        
        chat_ref.delete()
        return True
    
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        return False
