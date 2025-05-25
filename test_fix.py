#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for file_optimizer.py fix
"""

from file_optimizer import read_csv_optimized, convert_to_serializable
import numpy as np
import pandas as pd

def main():
    # Create a test DataFrame with various data types
    df = pd.DataFrame({
        'int_col': [1, 2, 3, np.int64(4)],
        'float_col': [1.1, 2.2, 3.3, np.float64(4.4)],
        'bool_col': [True, False, True, np.bool_(False)],
        'str_col': ['a', 'b', 'c', 'd']
    })
    
    # Test data to be serialized
    test_data = {
        'numpy_int': np.int64(42),
        'numpy_float': np.float64(3.14),
        'numpy_array': np.array([1, 2, 3]),
        'numpy_bool': np.bool_(True),
        'pandas_series': pd.Series([1, 2, 3]),
        'pandas_df': df,
        'nested_dict': {
            'a': np.int64(1),
            'b': [np.float64(2.0), np.float64(3.0)]
        },
        'nested_list': [np.int64(1), {'x': np.float64(2.0)}]
    }
    
    print("Testing convert_to_serializable function...")
    try:
        # Test the function
        serialized_data = convert_to_serializable(test_data)
        print("Serialization successful!")
        
        # Validate types in the serialized data
        print("\nValidating serialized data types:")
        print(f"numpy_int: {type(serialized_data['numpy_int']).__name__}")
        print(f"numpy_float: {type(serialized_data['numpy_float']).__name__}")
        print(f"numpy_array: {type(serialized_data['numpy_array']).__name__}")
        print(f"numpy_bool: {type(serialized_data['numpy_bool']).__name__}")
        print(f"pandas_series: {type(serialized_data['pandas_series']).__name__}")
        
        # Test JSON serialization
        import json
        json_str = json.dumps(serialized_data)
        print(f"\nJSON serialization successful! Length: {len(json_str)} characters")
        
        print("\nFix was successful!")
    except Exception as e:
        print(f"Error during serialization test: {e}")
        
if __name__ == "__main__":
    main()
