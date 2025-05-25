import numpy as np
import json
import pandas as pd
from file_optimizer import convert_to_serializable
from json_utils import EnhancedJSONEncoder

# Create test data with NumPy types
data = {
    'np_int64': np.int64(12345),
    'np_float64': np.float64(123.45),
    'np_array': np.array([1, 2, 3, 4, 5]),
    'np_bool': np.bool_(True),
    'nested': {
        'np_int32': np.int32(42),
        'array_with_int64': np.array([np.int64(1), np.int64(2), np.int64(3)])
    },
    'list_with_np': [1, 2, np.int64(3), 4, np.float32(5.0)],
    'pd_series': pd.Series([1, 2, 3, 4, 5]),
    'pd_dataframe': pd.DataFrame({'A': [1, 2, 3], 'B': ['a', 'b', 'c']})
}

print("Testing JSON serialization of complex NumPy/Pandas types")
print("-" * 50)
print("\nTest data structure:")
for key, value in data.items():
    print(f"{key}: {type(value)}")

# Test direct serialization (should fail)
try:
    print("\n1. Direct JSON serialization:")
    json_result = json.dumps(data)
    print(f"   Unexpected success: {len(json_result)} characters")
except TypeError as e:
    print(f"   Expected error: {e}")

# Test with our conversion function    
try:
    print("\n2. Using convert_to_serializable:")
    serializable_data = convert_to_serializable(data)
    json_result = json.dumps(serializable_data)
    print(f"   Success: {len(json_result)} characters")
except Exception as e:
    print(f"   Error: {e}")

# Test with enhanced encoder
try:
    print("\n3. Using EnhancedJSONEncoder:")
    json_result = json.dumps(data, cls=EnhancedJSONEncoder)
    print(f"   Success: {len(json_result)} characters")
except Exception as e:
    print(f"   Error: {e}")

print("\nTest completed")
