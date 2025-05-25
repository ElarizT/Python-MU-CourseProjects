#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CSV File Upload and Processing Test

This script simulates the file upload workflow to test that all components
work correctly together, including proper error handling and JSON serialization.
"""

import os
import json
import uuid
import pandas as pd
import numpy as np
from datetime import datetime

# Import our utility functions
from file_optimizer import read_csv_optimized, convert_to_serializable
from json_utils import EnhancedJSONEncoder, convert_to_json_serializable

def simulate_upload():
    """
    Simulate the file upload and processing workflow
    """
    print("\n== CSV UPLOAD AND PROCESSING TEST ==\n")
    
    # Create test directory if it doesn't exist
    upload_dir = './test_uploads'
    user_id = 'test_user_' + str(uuid.uuid4())[:8]
    user_upload_dir = os.path.join(upload_dir, user_id)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    print(f"Created upload directory: {user_upload_dir}")
    
    # Generate a unique filename
    unique_id = str(uuid.uuid4().hex[:8])
    original_filename = "test_dataset.csv"
    stored_filename = f"{unique_id}_{original_filename}"
    file_path = os.path.join(user_upload_dir, stored_filename)
    
    # Create a test CSV with NumPy datatypes
    print(f"Creating test CSV file: {file_path}")
    generate_test_csv(file_path)
    
    # Simulate file processing
    print("\nSimulating file processing...")
    
    start_time = datetime.now()
    try:
        # Extract text from CSV
        text, metadata, is_truncated, full_content_size = read_csv_optimized(file_path)
        
        print(f"File processed successfully:")
        print(f"- Text length: {len(text)} characters")
        print(f"- Metadata keys: {list(metadata.keys())}")
        print(f"- Truncated: {is_truncated}")
        
        # Prepare response data (similar to the endpoint)
        response_data = {
            'success': True,
            'filename': original_filename,
            'stored_filename': stored_filename,
            'message': 'File processed successfully',
            'content_preview': text[:200] + ('...' if len(text) > 200 else ''),
            'content': text[:1000] + ('...' if len(text) > 1000 else ''),  # Truncate for testing
            'is_truncated': is_truncated,
            'full_content_size': full_content_size,
            'metadata': metadata,  # May contain NumPy types
            'file_id': unique_id,
            'storage_type': 'local',
            'processing_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
        }
        
        # Test serialization
        print("\nTesting JSON serialization:")
        
        # 1. Using convert_to_serializable
        serializable_data = convert_to_serializable(response_data)
        json_result = json.dumps(serializable_data)
        print(f"1. Serialization with convert_to_serializable succeeded: {len(json_result)} characters")
        
        # 2. Using EnhancedJSONEncoder
        json_result = json.dumps(response_data, cls=EnhancedJSONEncoder) 
        print(f"2. Serialization with EnhancedJSONEncoder succeeded: {len(json_result)} characters")
        
        # 3. Using convert_to_json_serializable from json_utils.py
        serializable_data = convert_to_json_serializable(response_data)
        json_result = json.dumps(serializable_data)
        print(f"3. Serialization with convert_to_json_serializable succeeded: {len(json_result)} characters")
        
        print("\nAll serialization methods worked correctly!")
        
        # Simulate session storage
        print("\nSimulating session storage...")
        session_data = {
            'current_file': {
                'filename': original_filename,
                'stored_filename': stored_filename,
                'file_id': unique_id,
                'content': text,  # Store the full content for immediate access
                'is_truncated': is_truncated,  # Indicate if content was truncated
                'full_content_size': convert_to_serializable(full_content_size),  # Ensure int64 is converted
                'metadata': convert_to_serializable(metadata),  # Ensure metadata is serializable
                'upload_timestamp': datetime.now().isoformat()
            }
        }
        
        # Try serializing the session data
        json_result = json.dumps(session_data, cls=EnhancedJSONEncoder)
        print(f"Session data serialization succeeded: {len(json_result)} characters")
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        return False
    
    print("\nCleanup...")
    # Clean up the test files
    try:
        os.remove(file_path)
        os.rmdir(user_upload_dir)
        if os.path.exists(upload_dir) and not os.listdir(upload_dir):
            os.rmdir(upload_dir)
        print("Test files removed successfully")
    except Exception as e:
        print(f"Warning: Could not clean up test files: {e}")
    
    print("\nTest completed successfully!")
    return True

def generate_test_csv(file_path):
    """
    Generate a test CSV file with various data types
    """
    # Create a dataframe with different data types
    np.random.seed(42)  # For reproducibility
    
    # Generate 100 rows of synthetic data
    num_rows = 100
    
    data = {
        'id': np.arange(1, num_rows + 1),
        'int_value': np.random.randint(1, 1000, size=num_rows),
        'float_value': np.random.random(num_rows) * 100,
        'bool_value': np.random.choice([True, False], size=num_rows),
        'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], size=num_rows),
        'text': ['Text_' + str(i) for i in range(num_rows)]
    }
    
    df = pd.DataFrame(data)
    
    # Add some calculated columns with NumPy types
    df['int64_value'] = df['int_value'].astype(np.int64)
    df['float64_value'] = df['float_value'].astype(np.float64)
    df['bool_numpy'] = df['bool_value'].astype(np.bool_)
    
    # Convert category to pandas categorical type
    df['category'] = df['category'].astype('category')
    
    # Write to CSV
    df.to_csv(file_path, index=False)
    print(f"Generated CSV with {len(df)} rows and {len(df.columns)} columns")
    return file_path

if __name__ == "__main__":
    simulate_upload()
