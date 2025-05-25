import os
import json
import uuid
import tempfile
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import google.generativeai as genai
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import requests
import html
import re
import time

# Mock Firebase implementation for development/testing
print("Note: Using mock Firebase implementation for testing")

# Mock Firestore class
class MockFirestore:
    """Mock implementation of Firestore for testing without Firebase connection"""
    
    # Mock server timestamp implementation
    SERVER_TIMESTAMP = datetime.now()
    
    # Mock Increment implementation
    class Increment:
        def __init__(self, amount):
            self.amount = amount

# Mock DocumentReference class
class MockDocumentReference:
    """Mock implementation of Firestore DocumentReference"""
    
    def __init__(self, path):
        self.path = path
        self._data = {}
    
    def set(self, data, merge=False):
        if merge:
            self._data.update(data)
        else:
            self._data = data
        return self
    
    def update(self, data):
        self._data.update(data)
        return self
        
    def get(self):
        return MockDocumentSnapshot(self.path, self._data)
        
    def collection(self, collection_path):
        return MockCollectionReference(f"{self.path}/{collection_path}")

# Mock CollectionReference class
class MockCollectionReference:
    """Mock implementation of Firestore CollectionReference"""
    
    def __init__(self, path):
        self.path = path
        self._documents = {}
    
    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        return MockDocumentReference(f"{self.path}/{doc_id}")
    
    def where(self, field, op, value):
        # Just return self for chaining in mocks
        return self
        
    def order_by(self, field, direction='asc'):
        # Just return self for chaining in mocks
        return self
    
    def limit(self, count):
        # Just return self for chaining in mocks
        return self
    
    def stream(self):
        # Return empty list for now
        return []

# Mock DocumentSnapshot class
class MockDocumentSnapshot:
    """Mock implementation of Firestore DocumentSnapshot"""
    
    def __init__(self, path, data):
        self.path = path
        self._data = data
        self.reference = MockDocumentReference(path)
    
    def to_dict(self):
        return self._data
    
    def exists(self):
        return bool(self._data)

# Mock Database class
class MockDatabase:
    """Mock implementation of Firestore Database"""
    
    def collection(self, collection_path):
        return MockCollectionReference(collection_path)
    
    def batch(self):
        return MockWriteBatch()

# Mock WriteBatch class
class MockWriteBatch:
    """Mock implementation of Firestore WriteBatch"""
    
    def __init__(self):
        self.operations = []
    
    def set(self, doc_ref, data, merge=False):
        self.operations.append(('set', doc_ref, data, merge))
        return self
    
    def update(self, doc_ref, data):
        self.operations.append(('update', doc_ref, data))
        return self
    
    def delete(self, doc_ref):
        self.operations.append(('delete', doc_ref))
        return self
    
    def commit(self):
        # Just pretend we committed successfully
        return []

# Mock Storage implementation for development/testing
class MockStorage:
    """Mock implementation of Firebase Storage for testing without Firebase connection"""
    
    def __init__(self):
        self._files = {}
    
    def bucket(self, name=None):
        return MockBucket(name or "default-bucket")

class MockBucket:
    """Mock implementation of Firebase Storage Bucket"""
    
    def __init__(self, name):
        self.name = name
        self._blobs = {}
    
    def blob(self, path):
        return MockBlob(path, self)
        
    def get_blob(self, path):
        if path in self._blobs:
            return self._blobs[path]
        return None

class MockBlob:
    """Mock implementation of Firebase Storage Blob"""
    
    def __init__(self, path, bucket):
        self.path = path
        self.bucket = bucket
        self._data = None
        self._metadata = {}
    
    def upload_from_file(self, file_obj, content_type=None):
        file_obj.seek(0)
        self._data = file_obj.read()
        file_obj.seek(0)
        if content_type:
            self._metadata["contentType"] = content_type
        self.bucket._blobs[self.path] = self
        return self
        
    def upload_from_filename(self, filename):
        with open(filename, 'rb') as f:
            self._data = f.read()
        self.bucket._blobs[self.path] = self
        return self
        
    def download_to_filename(self, filename):
        with open(filename, 'wb') as f:
            f.write(self._data)
        return filename
        
    def download_as_bytes(self):
        return self._data
        
    def generate_signed_url(self, expiration, method="GET"):
        return f"mock-signed-url/{self.path}"
        
    def delete(self):
        if self.path in self.bucket._blobs:
            del self.bucket._blobs[self.path]
        return True
    
    def exists(self):
        return self._data is not None
        
    def metadata(self):
        return self._metadata

# Initialize mock instances
db = MockDatabase()
firestore = MockFirestore()
storage = MockStorage()

# Function to check if real Firebase is available
def is_firebase_available():
    try:
        # Check if firebase_admin is installed
        import firebase_admin
        from firebase_admin import credentials, firestore, storage
        
        # Get storage bucket name from environment variable - keep the original format
        storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET', 'lightyearai-app.firebasestorage.app')
        
        # We'll use the bucket name as-is instead of trying to convert it
        if not storage_bucket:
            print("Warning: FIREBASE_STORAGE_BUCKET environment variable not set. Using default bucket name.")
        else:
            print(f"Using Firebase Storage bucket: {storage_bucket}")
        
        # Check for credentials in various locations
        possible_cred_paths = [
            os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
            os.environ.get('FIREBASE_CREDENTIALS_PATH'),
            'lightyearai-app-firebase-adminsdk-fbsvc-a1c778d686.json',
            '/etc/firebase/credentials.json'
        ]
        
        # Also check if credentials are provided as base64 encoded string in environment variable
        firebase_credentials_base64 = os.environ.get('FIREBASE_CREDENTIALS_BASE64')
        
        cred = None
        cred_file = None
        
        # Try to load credentials from base64 content first
        if firebase_credentials_base64:
            try:
                import base64
                import json
                import tempfile
                
                # Decode the base64 string to JSON content
                json_content = base64.b64decode(firebase_credentials_base64).decode('utf-8')
                
                # Write the JSON to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.json') as tmp_file:
                    tmp_file.write(json_content)
                    cred_file = tmp_file.name
                
                cred = credentials.Certificate(cred_file)
                print(f"Using Firebase credentials from FIREBASE_CREDENTIALS_BASE64 environment variable")
            except Exception as e:
                print(f"Error loading credentials from base64: {e}")
        
        # If we couldn't load from base64, try the file paths
        if not cred:
            for path in possible_cred_paths:
                if path and os.path.exists(path):
                    cred_file = path
                    cred = credentials.Certificate(cred_file)
                    print(f"Using Firebase credentials file: {cred_file}")
                    break
        
        if not cred:
            print("Warning: No Firebase credentials file found. Using local file storage instead.")
            print("To use Firebase Cloud Storage, please set FIREBASE_CREDENTIALS_BASE64 environment variable.")
            return False
        
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket
            })
        
        return True
    except ImportError as e:
        print(f"Firebase admin SDK import error: {e}")
        return False
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        return False

# Try to initialize real Firebase if available
if is_firebase_available():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore as fb_firestore, storage as fb_storage
        
        # Replace mocks with real implementations
        db = fb_firestore.client()
        firestore = fb_firestore
        storage = fb_storage
        
        print("Using real Firebase connection")
    except Exception as e:
        print(f"Failed to initialize real Firebase: {e}")
        print("Falling back to mock implementation")
else:
    print("Firebase not available. Using mock Firebase implementation.")

# Chat History Functions
def save_chat_message(user_id, chat_type, message, role="user"):
    """
    Save a chat message to Firestore.
    
    Args:
        user_id (str): User ID
        chat_type (str): Type of chat (e.g., 'study', 'entertainment')
        message (str): The message content
        role (str): Role of the sender ('user' or 'assistant')
    
    Returns:
        str: ID of the saved message or None if failed
    """
    if not user_id:
        print("Cannot save chat message: No user ID provided")
        # Instead of just returning None, we'll create a session-only message
        # This allows the chat to work even if the user ID is missing
        from datetime import datetime
        return f"temp-{datetime.now().timestamp()}"
    
    try:
        # Create a new message document with timestamp
        message_data = {
            'content': message,
            'role': role,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'chat_type': chat_type
        }
        
        # Add to user's chat collection
        message_ref = db.collection('users').document(user_id).collection('chat_history').document()
        message_ref.set(message_data)
        
        return message_ref.id
    except Exception as e:
        print(f"Error saving chat message: {e}")
        # Return a temporary ID so the chat can continue
        from datetime import datetime
        return f"temp-{datetime.now().timestamp()}"

def get_chat_history(user_id, chat_type, limit=50):
    """
    Get chat history for a specific user and chat type.
    
    Args:
        user_id (str): User ID
        chat_type (str): Type of chat ('study', 'entertainment', etc.)
        limit (int): Maximum number of messages to retrieve (default: 50)
    
    Returns:
        list: List of chat messages in chronological order
    """
    if not user_id:
        print("Cannot get chat history: No user ID provided")
        # Return empty list instead of failing
        return []
    
    try:
        # Modified query approach that doesn't require a composite index
        # First, get all chat history for this user
        messages_ref = (db.collection('users')
                       .document(user_id)
                       .collection('chat_history')
                       .limit(limit * 2))  # Get more than needed initially
        
        # Then filter in memory
        messages = []
        for doc in messages_ref.stream():
            message_data = doc.to_dict()
            doc_chat_type = message_data.get('chat_type')
            
            # Only include messages matching the requested chat_type
            if doc_chat_type == chat_type:
                message_data['id'] = doc.id
                
                # Convert Firebase timestamp to comparable value if it exists
                timestamp = message_data.get('timestamp')
                if hasattr(timestamp, 'seconds'):
                    # Convert Firebase timestamp to numeric value for sorting
                    message_data['timestamp_value'] = timestamp.seconds + (timestamp.nanos / 1e9)
                elif isinstance(timestamp, (int, float)):
                    message_data['timestamp_value'] = timestamp
                else:
                    # If no valid timestamp, use document ID for ordering (fallback)
                    message_data['timestamp_value'] = doc.id
                
                messages.append(message_data)
        
        # Sort by timestamp_value for more reliable ordering
        messages.sort(key=lambda x: x.get('timestamp_value', 0))
        
        # Limit to requested number after filtering
        return messages[:limit]
    except Exception as e:
        print(f"Error getting chat history: {e}")
        # In case of error, return empty list instead of failing
        return []

def delete_chat_history(user_id, chat_type=None, message_ids=None):
    """
    Delete chat history for a user.
    
    Args:
        user_id (str): User ID
        chat_type (str, optional): Type of chat to delete. If None, deletes based on message_ids
        message_ids (list, optional): List of specific message IDs to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not user_id:
        print("Cannot delete chat history: No user ID provided")
        return False
    
    try:
        batch = db.batch()
        
        if message_ids:
            # Delete specific messages
            for message_id in message_ids:
                message_ref = db.collection('users').document(user_id).collection('chat_history').document(message_id)
                batch.delete(message_ref)
        elif chat_type:
            # Delete all messages of a specific chat type
            # Note: Firestore doesn't directly support collection deletion with conditions,
            # so we need to fetch all matching documents and then batch delete them
            messages_ref = (db.collection('users')
                          .document(user_id)
                          .collection('chat_history')
                          .where('chat_type', '==', chat_type)
                          .limit(500))  # Limit for safety
            
            for doc in messages_ref.stream():
                batch.delete(doc.reference)
        else:
            # If neither chat_type nor message_ids provided, raise an error
            raise ValueError("Either chat_type or message_ids must be provided")
        
        # Commit the batch
        batch.commit()
        return True
    except Exception as e:
        print(f"Error deleting chat history: {e}")
        return False

def format_chat_history_for_api(messages):
    """
    Format chat history messages for API.
    
    Args:
        messages (list): List of chat messages from Firestore
    
    Returns:
        list: List of messages formatted for the model API
    """
    # Gemini API expects messages as part of a conversation history to be formatted as:
    # [
    #   {"role": "user", "parts": [{"text": "user message"}]},
    #   {"role": "model", "parts": [{"text": "model response"}]}
    # ]
    
    formatted_messages = []
    
    for message in messages:
        role = message.get('role', 'user')
        # Map 'assistant' role to 'model' as expected by Gemini
        if role == 'assistant':
            role = 'model'
            
        formatted_messages.append({
            'role': role,
            'parts': [{'text': message.get('content', '')}]
        })
    
    return formatted_messages

# File Storage Functions
def upload_file_to_storage(file_obj, filename, user_id, content_type=None):
    """
    Upload a file to Firebase Storage.
    
    Args:
        file_obj: File object to upload
        filename (str): Name of the file
        user_id (str): ID of the user who uploaded the file
        content_type (str, optional): Content type of the file
    
    Returns:
        dict: Dictionary with file metadata including download URL
    """
    try:
        # Generate a unique filename to avoid collisions
        unique_id = str(uuid.uuid4())
        safe_filename = secure_filename(filename)
        storage_path = f"uploads/{user_id}/{unique_id}_{safe_filename}"
        
        # Get the default bucket
        try:
            bucket = storage.bucket()
            
            # Create a blob and upload the file
            blob = bucket.blob(storage_path)
            blob.upload_from_file(file_obj, content_type=content_type)
            
            # Create a download URL that expires in 7 days (604800 seconds)
            download_url = blob.generate_signed_url(
                expiration=datetime.now() + timedelta(days=7),
                method="GET"
            )
            
            # Save metadata in Firestore
            file_metadata = {
                'filename': safe_filename,
                'storage_path': storage_path,
                'content_type': content_type,
                'upload_timestamp': firestore.SERVER_TIMESTAMP,
                'user_id': user_id,
                'size': len(file_obj.read()) if hasattr(file_obj, 'read') else 0
            }
            
            # Reset file pointer after reading size
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            
            # Store metadata in Firestore
            file_ref = db.collection('files').document(unique_id)
            file_ref.set(file_metadata)
            
            # Return the file information
            return {
                'file_id': unique_id,
                'filename': safe_filename,
                'storage_path': storage_path,
                'download_url': download_url,
                'content_type': content_type
            }
        except Exception as bucket_error:
            # If Firebase Storage fails, log the error and return None to trigger local storage fallback
            print(f"Error uploading file to Firebase Storage, will use local storage instead: {bucket_error}")
            
            # Reset file pointer to beginning for potential reuse in local storage fallback
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
                
            return None
            
    except Exception as e:
        print(f"Error uploading file to storage: {e}")
        
        # Reset file pointer to beginning for potential reuse in local storage fallback
        if hasattr(file_obj, 'seek'):
            file_obj.seek(0)
            
        return None

def upload_local_file_to_storage(file_path, user_id, original_filename=None):
    """
    Upload a local file to Firebase Storage.
    
    Args:
        file_path (str): Path to the local file
        user_id (str): ID of the user who uploaded the file
        original_filename (str, optional): Original name of the file
    
    Returns:
        dict: Dictionary with file metadata including download URL
    """
    try:
        # If no original filename provided, use the filename from the path
        if not original_filename:
            original_filename = os.path.basename(file_path)
        
        # Get content type based on file extension
        import mimetypes
        content_type, _ = mimetypes.guess_type(original_filename)
        
        # Generate a unique filename to avoid collisions
        unique_id = str(uuid.uuid4())
        safe_filename = secure_filename(original_filename)
        storage_path = f"uploads/{user_id}/{unique_id}_{safe_filename}"
        
        # Get the default bucket
        bucket = storage.bucket()
        
        # Create a blob and upload the file
        blob = bucket.blob(storage_path)
        blob.upload_from_filename(file_path)
        
        # Create a download URL that expires in 7 days (604800 seconds)
        download_url = blob.generate_signed_url(
            expiration=datetime.now() + timedelta(days=7),
            method="GET"
        )
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Save metadata in Firestore
        file_metadata = {
            'filename': safe_filename,
            'storage_path': storage_path,
            'content_type': content_type,
            'upload_timestamp': firestore.SERVER_TIMESTAMP,
            'user_id': user_id,
            'size': file_size
        }
        
        # Store metadata in Firestore
        file_ref = db.collection('files').document(unique_id)
        file_ref.set(file_metadata)
        
        # Return the file information
        return {
            'file_id': unique_id,
            'filename': safe_filename,
            'storage_path': storage_path,
            'download_url': download_url,
            'content_type': content_type
        }
    except Exception as e:
        print(f"Error uploading local file to storage: {e}")
        return None

def get_file_from_storage(file_id):
    """
    Get a file from Firebase Storage by its ID.
    
    Args:
        file_id (str): ID of the file
    
    Returns:
        dict: Dictionary with file metadata including download URL
    """
    try:
        # Get file metadata from Firestore
        file_ref = db.collection('files').document(file_id)
        file_doc = file_ref.get()
        
        if not file_doc.exists:
            print(f"File with ID {file_id} not found in Firestore")
            return None
        
        file_metadata = file_doc.to_dict()
        storage_path = file_metadata.get('storage_path')
        
        if not storage_path:
            print(f"No storage path found for file ID {file_id}")
            return None
        
        # Get the default bucket
        bucket = storage.bucket()
        
        # Get the blob
        blob = bucket.blob(storage_path)
        
        # Check if blob exists
        if not blob.exists():
            print(f"Blob not found at path {storage_path} for file ID {file_id}")
            return None
        
        # Create a download URL that expires in 7 days (604800 seconds)
        download_url = blob.generate_signed_url(
            expiration=datetime.now() + timedelta(days=7),
            method="GET"
        )
        
        # Update metadata with download URL
        file_metadata['download_url'] = download_url
        file_metadata['file_id'] = file_id  # Ensure file_id is included
        
        print(f"Successfully retrieved file {file_id} from storage with download URL")
        return file_metadata
    except Exception as e:
        print(f"Error getting file from storage: {e}")
        return None

def download_file_content(file_id_or_url):
    """
    Download and extract text content from a file in Firebase Storage.
    
    Args:
        file_id_or_url (str): Either the file ID or a download URL
    
    Returns:
        str: Extracted text content or None if failed
    """
    try:
        download_url = None
        file_metadata = None
        
        # Debug log
        print(f"[FIREBASE DEBUG] Attempting to download file content for: {file_id_or_url}")
        
        # Check if input is a URL or file ID
        if file_id_or_url and file_id_or_url.startswith(('http://', 'https://')):
            download_url = file_id_or_url
            print(f"[FIREBASE DEBUG] Using direct URL: {download_url[:50]}...")
        else:
            # Get file metadata and download URL from file ID
            print(f"[FIREBASE DEBUG] Looking up metadata for file ID: {file_id_or_url}")
            file_metadata = get_file_from_storage(file_id_or_url)
            if file_metadata:
                download_url = file_metadata.get('download_url')
                print(f"[FIREBASE DEBUG] Found download URL from metadata: {download_url[:50] if download_url else 'None'}...")
                print(f"[FIREBASE DEBUG] File metadata: {file_metadata}")
            else:
                print(f"[FIREBASE DEBUG] No metadata found for file ID: {file_id_or_url}")
        
        if not download_url:
            print(f"[FIREBASE DEBUG] ERROR: No valid download URL found for {file_id_or_url}")
            return None
        
        # Download the file to a temporary location
        import tempfile
        import os
        import requests
        
        # Get file extension from metadata or URL
        file_extension = '.pdf'  # Default to PDF
        if file_metadata and 'filename' in file_metadata:
            _, file_extension = os.path.splitext(file_metadata['filename'])
            print(f"[FIREBASE DEBUG] Using file extension: {file_extension} from filename: {file_metadata.get('filename')}")
        
        # Create a temporary file with the correct extension
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
        temp_file.close()
        print(f"[FIREBASE DEBUG] Created temporary file: {temp_file.name}")
        
        # Download the file
        response = requests.get(download_url)
        if response.status_code != 200:
            print(f"[FIREBASE DEBUG] Failed to download file: HTTP status {response.status_code}")
            os.unlink(temp_file.name)
            return None
        
        # Save the content to the temporary file
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)
        
        print(f"[FIREBASE DEBUG] Downloaded file size: {len(response.content)} bytes")
        print(f"[FIREBASE DEBUG] File saved to temporary location: {temp_file.name}")
        print(f"[FIREBASE DEBUG] File exists check: {os.path.exists(temp_file.name)}")
        print(f"[FIREBASE DEBUG] File size check: {os.path.getsize(temp_file.name)} bytes")
        
        # Extract text from the file
        from file_utils import extract_text_from_file
        text_content = extract_text_from_file(temp_file.name)
        
        # Log text extraction results
        if text_content:
            text_length = len(text_content)
            print(f"[FIREBASE DEBUG] Extracted text length: {text_length} characters")
            print(f"[FIREBASE DEBUG] Text sample (first 100 chars): {text_content[:100]}")
            # Count words as a sanity check
            word_count = len(text_content.split())
            print(f"[FIREBASE DEBUG] Approximate word count: {word_count} words")
        else:
            print(f"[FIREBASE DEBUG] Warning: No text content was extracted from the file")
        
        # Clean up
        try:
            os.unlink(temp_file.name)
            print(f"[FIREBASE DEBUG] Temporary file cleaned up: {temp_file.name}")
        except Exception as cleanup_err:
            print(f"[FIREBASE DEBUG] Error during temp file cleanup: {cleanup_err}")
        
        return text_content
    except Exception as e:
        print(f"[FIREBASE DEBUG] Error downloading file content: {e}")
        import traceback
        traceback.print_exc()
        return None

def download_file_from_storage(file_id, destination_path):
    """
    Download a file from Firebase Storage by its ID.
    
    Args:
        file_id (str): ID of the file
        destination_path (str): Path where the file should be saved
    
    Returns:
        str: Path to the downloaded file or None if failed
    """
    try:
        # Get file metadata from Firestore
        file_ref = db.collection('files').document(file_id)
        file_doc = file_ref.get()
        
        if not file_doc.exists:
            return None
        
        file_metadata = file_doc.to_dict()
        storage_path = file_metadata.get('storage_path')
        
        # Get the default bucket
        bucket = storage.bucket()
        
        # Get the blob
        blob = bucket.blob(storage_path)
        
        # Download the file
        blob.download_to_filename(destination_path)
        
        return destination_path
    except Exception as e:
        print(f"Error downloading file from storage: {e}")
        return None

def delete_file_from_storage(file_id):
    """
    Delete a file from Firebase Storage by its ID.
    
    Args:
        file_id (str): ID of the file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get file metadata from Firestore
        file_ref = db.collection('files').document(file_id)
        file_doc = file_ref.get()
        
        if not file_doc.exists:
            return False
        
        file_metadata = file_doc.to_dict()
        storage_path = file_metadata.get('storage_path')
        
        # Get the default bucket
        bucket = storage.bucket()
        
        # Get the blob
        blob = bucket.blob(storage_path)
        
        # Delete the blob
        blob.delete()
        
        # Delete the metadata from Firestore
        file_ref.delete()
        
        return True
    except Exception as e:
        print(f"Error deleting file from storage: {e}")
        return False

def get_user_files(user_id, limit=50):
    """
    Get all files uploaded by a user.
    
    Args:
        user_id (str): ID of the user
        limit (int): Maximum number of files to retrieve
    
    Returns:
        list: List of file metadata
    """
    print(f"DEBUG: get_user_files called for user_id: {user_id}")
    try:
        # Check if Firebase is available
        if not is_firebase_available():
            print(f"DEBUG: Firebase not available when fetching files for user: {user_id}")
            return []
            
        # Get files from Firestore
        print(f"DEBUG: Querying Firestore for files with user_id: {user_id}")
        
        # FIXED: Query from 'files' collection AND 'user_files' collection (both are used in uploads)
        # Some files are saved in 'files' collection
        files_ref = db.collection('files').where('user_id', '==', user_id).limit(limit)
        
        # Get all files and add download URLs
        files = []
        doc_count = 0
        
        # First get files from 'files' collection
        for doc in files_ref.stream():
            doc_count += 1
            file_metadata = doc.to_dict()
            file_metadata['file_id'] = doc.id
            
            print(f"DEBUG: Found file document with ID: {doc.id} in 'files' collection")
            
            # Get the download URL
            storage_path = file_metadata.get('storage_path')
            if storage_path:
                print(f"DEBUG: Getting download URL for storage path: {storage_path}")
                bucket = storage.bucket()
                blob = bucket.blob(storage_path)
                
                try:
                    if not blob.exists():
                        print(f"DEBUG: Blob does not exist at path: {storage_path}")
                        continue
                    
                    # Create a download URL that expires in 7 days (604800 seconds)
                    download_url = blob.generate_signed_url(
                        expiration=datetime.now() + timedelta(days=7),
                        method="GET"
                    )
                    
                    file_metadata['download_url'] = download_url
                    file_metadata['name'] = file_metadata.get('filename', 'Unknown file name')
                except Exception as blob_error:
                    print(f"DEBUG: Error getting blob URL: {blob_error}")
                    continue
            else:
                print(f"DEBUG: No storage path found for file ID: {doc.id}")
                continue
            
            files.append(file_metadata)
        
        # FIXED: Also check in 'user_files' collection where some files might be stored
        user_files_ref = db.collection('user_files').where('user_id', '==', user_id).limit(limit)
        for doc in user_files_ref.stream():
            doc_count += 1
            file_metadata = doc.to_dict()
            file_metadata['file_id'] = doc.id
            
            print(f"DEBUG: Found file document with ID: {doc.id} in 'user_files' collection")
            
            # Get the download URL
            storage_path = file_metadata.get('storage_path')
            download_url = file_metadata.get('download_url')
            
            if storage_path and not download_url:
                print(f"DEBUG: Getting download URL for storage path: {storage_path}")
                bucket = storage.bucket()
                blob = bucket.blob(storage_path)
                
                try:
                    if not blob.exists():
                        print(f"DEBUG: Blob does not exist at path: {storage_path}")
                        continue
                    
                    # Create a download URL that expires in 7 days (604800 seconds)
                    download_url = blob.generate_signed_url(
                        expiration=datetime.now() + timedelta(days=7),
                        method="GET"
                    )
                    
                    file_metadata['download_url'] = download_url
                except Exception as blob_error:
                    print(f"DEBUG: Error getting blob URL: {blob_error}")
                    continue
            
            # Set name for display
            file_metadata['name'] = file_metadata.get('filename', 'Unknown file name')
            
            files.append(file_metadata)
        
        print(f"DEBUG: Found {doc_count} documents, returning {len(files)} valid files")
        return files
    except Exception as e:
        print(f"Error getting user files: {e}")
        import traceback
        traceback.print_exc()
        return []