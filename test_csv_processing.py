import os
import json
from file_optimizer import read_csv_optimized, convert_to_serializable
from json_utils import EnhancedJSONEncoder

# Create a simple test CSV file
test_csv_path = "test_data.csv"
with open(test_csv_path, "w") as f:
    f.write("id,name,age,score\n")
    f.write("1,John,30,95.5\n")
    f.write("2,Jane,25,98.7\n")
    f.write("3,Bob,40,85.2\n")

print(f"Created test CSV file: {test_csv_path}")

# Process the CSV file
try:
    print("\nProcessing CSV file...")
    text, metadata, is_truncated, full_content_size = read_csv_optimized(test_csv_path)
    
    print(f"Text content length: {len(text)}")
    print(f"Metadata keys: {list(metadata.keys())}")
    print(f"Is truncated: {is_truncated}")
    print(f"Full content size: {full_content_size}")
    
    # Test JSON serialization
    print("\nTesting JSON serialization...")
    
    # 1. First try direct serialization (this should fail with NumPy types)
    try:
        json_result = json.dumps(metadata)
        print("Direct JSON serialization succeeded (unexpected)")
    except TypeError as e:
        print(f"Expected serialization error: {e}")
        
        # 2. Now try with our custom converter
        serializable_metadata = convert_to_serializable(metadata)
        json_result = json.dumps(serializable_metadata)
        print(f"Serialization with convert_to_serializable succeeded: {len(json_result)} characters")
        
        # 3. Try with EnhancedJSONEncoder
        json_result = json.dumps(metadata, cls=EnhancedJSONEncoder)
        print(f"Serialization with EnhancedJSONEncoder succeeded: {len(json_result)} characters")
    
    print("\nTest completed successfully")
    
except Exception as e:
    print(f"Error during test: {e}")

# Clean up
if os.path.exists(test_csv_path):
    os.remove(test_csv_path)
    print(f"\nRemoved test file: {test_csv_path}")
