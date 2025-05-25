import os
import uuid
from werkzeug.utils import secure_filename

# Simulate app configuration
app_config = {'UPLOAD_FOLDER': './uploads'}
user_id = 'test_user'

# Create user upload directory
user_upload_dir = os.path.join(app_config['UPLOAD_FOLDER'], user_id)
os.makedirs(user_upload_dir, exist_ok=True)

# Generate unique filename 
unique_id = str(uuid.uuid4().hex[:8])
original_filename = secure_filename('test_file.csv')
stored_filename = f"{unique_id}_{original_filename}"

# Create file path
file_path = os.path.join(user_upload_dir, stored_filename)

print(f"User upload directory: {user_upload_dir}")
print(f"Generated filename: {stored_filename}")
print(f"Complete file path: {file_path}")
print(f"Directory exists: {os.path.exists(os.path.dirname(file_path))}")

# Create a test file 
with open(file_path, 'w') as f:
    f.write("test content")

print(f"File created successfully: {os.path.exists(file_path)}")
