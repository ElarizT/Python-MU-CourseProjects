#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test to verify that the convert_to_serializable function works correctly in app.py context
"""

import os
import sys
import pandas as pd
import numpy as np

# Import the core app functions but don't run the app
from app import convert_to_serializable

def test_convert_to_serializable():
    """Test that the function correctly serializes NumPy and Pandas objects"""
    print("Testing convert_to_serializable function in app.py context...")
    
    # Create test data with various types
    test_data = {
        'numpy_int': np.int64(42),
        'numpy_float': np.float64(3.14),
        'numpy_array': np.array([1, 2, 3]),
        'nested_dict': {
            'a': np.int64(1),
            'b': [np.float64(2.0), np.float64(3.0)]
        }
    }
    
    # Test the function
    try:
        serialized_data = convert_to_serializable(test_data)
        print("Serialization successful!")
        
        # Validate types
        assert isinstance(serialized_data['numpy_int'], int)
        assert isinstance(serialized_data['numpy_float'], float)
        assert isinstance(serialized_data['numpy_array'], list)
        assert isinstance(serialized_data['nested_dict']['a'], int)
        assert isinstance(serialized_data['nested_dict']['b'][0], float)
        
        print("All type checks passed!")
        
        # Try JSON serializing the result
        import json
        json_result = json.dumps(serialized_data)
        print(f"JSON serialization successful! Length: {len(json_result)} characters")
        
        return True
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False
        
if __name__ == "__main__":
    import traceback
    success = test_convert_to_serializable()
    print(f"Test {'succeeded' if success else 'failed'}!")
