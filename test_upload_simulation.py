import os
import numpy as np
import pandas as pd
import json
from file_optimizer import read_csv_optimized, convert_to_serializable
from json_utils import EnhancedJSONEncoder

# Simulate safe_jsonify from app.py
def safe_jsonify(data):
    """
    A safer version of jsonify that handles non-JSON-serializable types like NumPy arrays/values.
    Falls back to string representation for truly unserializable objects.
    """
    try:
        # First try normal json dumps
        return json.dumps(data)
    except (TypeError, ValueError, OverflowError) as e:
        # On serialization error, try to convert the data
        try:
            from json_utils import convert_to_json_serializable
            serializable_data = convert_to_serializable(data)
            return json.dumps(serializable_data)
        except Exception as e2:
            # If all else fails, return an error message
            print(f"JSON Serialization Error: {e} -> {e2}")
            return json.dumps({
                'error': 'Failed to serialize response',
                'details': str(e)
            })

# Create a more complex test CSV with values that will generate NumPy types
test_csv_path = "complex_test.csv"
with open(test_csv_path, "w") as f:
    f.write("id,name,age,score,is_active,graduation_date\n")
    for i in range(1, 21):  # 20 rows of data
        f.write(f"{i},Person{i},{20+i},{85+i*0.5},{i%2==0},2023-{i%12+1:02d}-{i%28+1:02d}\n")

print(f"Created complex test CSV file: {test_csv_path}")

# Simulate the file upload process
try:
    print("\nProcessing CSV file...")
    # 1. Read and process the CSV file
    text, metadata, is_truncated, full_content_size = read_csv_optimized(test_csv_path)
    
    print(f"Text content length: {len(text)}")
    print(f"Metadata keys: {list(metadata.keys())}")
    print(f"Is truncated: {is_truncated}")
    print(f"Full content size: {full_content_size}")
    
    # 2. Prepare the response data (similar to the endpoint)
    response_data = {
        'success': True,
        'filename': test_csv_path,
        'stored_filename': 'test_' + test_csv_path,
        'message': 'File processed successfully',
        'content_preview': text[:200] + ('...' if len(text) > 200 else ''),
        'content': text,
        'is_truncated': is_truncated,
        'full_content_size': full_content_size,
        'metadata': metadata,  # Include metadata, may contain NumPy types
        'file_id': '12345',
        'storage_type': 'local',
    }
    
    # 3. Test JSON serialization with different methods
    print("\nTesting response serialization:")
    
    # Direct serialization - should fail with NumPy values
    try:
        print("\n1. Direct JSON serialization:")
        json_result = json.dumps(response_data)
        print(f"   Unexpected success: {len(json_result)} characters")
    except TypeError as e:
        print(f"   Expected error: {e}")
        
    # Using convert_to_serializable
    try:
        print("\n2. Using convert_to_serializable:")
        serializable_data = convert_to_serializable(response_data)
        json_result = json.dumps(serializable_data)
        print(f"   Success: {len(json_result)} characters")
    except Exception as e:
        print(f"   Error: {e}")
        
    # Using EnhancedJSONEncoder
    try:
        print("\n3. Using EnhancedJSONEncoder:")
        json_result = json.dumps(response_data, cls=EnhancedJSONEncoder)
        print(f"   Success: {len(json_result)} characters")
    except Exception as e:
        print(f"   Error: {e}")
        
    # Using safe_jsonify (our safe fallback method)
    try:
        print("\n4. Using safe_jsonify:")
        json_result = safe_jsonify(response_data)
        print(f"   Success: {len(json_result)} characters")
    except Exception as e:
        print(f"   Error: {e}")
        
    print("\nTest completed successfully")
    
except Exception as e:
    print(f"Error during test: {e}")

# Clean up
if os.path.exists(test_csv_path):
    os.remove(test_csv_path)
    print(f"\nRemoved test file: {test_csv_path}")
