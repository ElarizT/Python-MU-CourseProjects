import base64
import sys

def encode_firebase_credentials(file_path):
    """Read a Firebase credentials JSON file and encode it to a clean Base64 string"""
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        # Encode to base64
        encoded = base64.b64encode(file_content)
        
        # Convert to string without newlines and ensure proper padding
        encoded_str = encoded.decode("utf-8")
        
        # Ensure padding is correct (base64 should have length as a multiple of 4)
        padding_needed = len(encoded_str) % 4
        if padding_needed:
            encoded_str += '=' * (4 - padding_needed)
        
        print("Successfully encoded Firebase credentials")
        print("-" * 40)
        print("Copy this string to your FIREBASE_CREDENTIALS_BASE64 environment variable in Render.com:")
        print(encoded_str)
        print("-" * 40)
        return encoded_str
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python encode_firebase_credentials.py <path_to_credentials_json>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    encode_firebase_credentials(file_path)

