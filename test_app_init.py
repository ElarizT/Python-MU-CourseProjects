"""
Test script to check if the Flask application initializes properly
without the duplicate endpoint error.
"""
import sys
import os

# Add the current directory to the path
sys.path.append(os.getcwd())

try:
    print("Attempting to initialize Flask app...")
    from app import app
    print("SUCCESS: Flask app initialized successfully without errors.")
    print("The duplicate endpoint issue has been fixed.")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {str(e)}")
    print("The app still has initialization issues.")
