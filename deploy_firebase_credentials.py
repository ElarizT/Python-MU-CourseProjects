#!/usr/bin/env python
"""
Firebase Credentials Deployment Helper Script
This script helps deploy Firebase credentials to a hosting environment.
"""

import os
import json
import base64
import argparse
import sys

def encode_credentials_file(file_path):
    """Encode the Firebase credentials file to base64 for environment variable storage"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Encode to base64
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        print(f"Successfully encoded credentials file: {file_path}")
        
        # Print instructions
        print("\n===== DEPLOYMENT INSTRUCTIONS =====")
        print("Add the following environment variable to your hosting platform:")
        print("FIREBASE_CREDENTIALS_BASE64")
        print("\nThe encoded value is:")
        print(encoded)
        print("\n==================================")
        
        return encoded
    except Exception as e:
        print(f"Error encoding credentials file: {str(e)}")
        return None

def verify_credentials(encoded_data):
    """Verify that the encoded credentials can be properly decoded"""
    try:
        # Decode the base64 string
        decoded = base64.b64decode(encoded_data).decode('utf-8')
        
        # Try to parse as JSON
        creds_json = json.loads(decoded)
        
        # Check for required fields
        required_fields = [
            "type", 
            "project_id", 
            "private_key_id", 
            "private_key", 
            "client_email"
        ]
        
        for field in required_fields:
            if field not in creds_json:
                print(f"Warning: Missing required field '{field}' in credentials")
                
        print("✅ Credentials successfully verified!")
        return True
    except json.JSONDecodeError:
        print("❌ Error: Decoded data is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error verifying credentials: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Firebase Credentials Deployment Helper")
    parser.add_argument("--file", "-f", help="Path to Firebase credentials JSON file")
    parser.add_argument("--verify", "-v", help="Verify an encoded base64 string", action="store_true")
    
    args = parser.parse_args()
    
    if args.file:
        encoded = encode_credentials_file(args.file)
        if encoded and args.verify:
            verify_credentials(encoded)
    elif args.verify:
        # Read from environment variable or stdin
        if "FIREBASE_CREDENTIALS_BASE64" in os.environ:
            encoded = os.environ["FIREBASE_CREDENTIALS_BASE64"]
            print("Using credentials from FIREBASE_CREDENTIALS_BASE64 environment variable")
        else:
            print("Enter encoded base64 credentials string:")
            encoded = input().strip()
            
        verify_credentials(encoded)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
