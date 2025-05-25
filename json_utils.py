#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
JSON serialization utilities for LightYearAI app

This module provides helper functions and classes for proper JSON serialization,
especially for handling NumPy and other scientific data types that are not
natively JSON serializable.
"""

import json
from datetime import datetime
import numpy as np

# Try different import paths for JSONEncoder based on Flask version
try:
    from flask.json import JSONEncoder
except ImportError:
    try:
        from flask.json.provider import JSONEncoder
    except ImportError:
        # Fallback to standard json
        from json import JSONEncoder

class EnhancedJSONEncoder(JSONEncoder):
    """
    Custom JSON encoder that properly handles:
    - NumPy integers, floats, and arrays
    - Pandas Series and DataFrames
    - Datetime objects
    - Any other special types we need to serialize
    """
    def default(self, obj):
        # Handle NumPy types
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        # Handle datetime objects
        elif isinstance(obj, datetime):
            return obj.isoformat()
        # Handle pandas Series and DataFrames if available
        elif str(type(obj)).startswith("<class 'pandas."):
            try:
                return obj.to_dict()
            except:
                return str(obj)
        # Let the base class handle anything else
        return super(EnhancedJSONEncoder, self).default(obj)


def convert_to_json_serializable(obj):
    """
    Recursively convert any object to a JSON serializable type.
    
    Args:
        obj: Any Python object
        
    Returns:
        A JSON-serializable version of the object
    """
    if obj is None:
        return None
    elif hasattr(np, 'integer') and isinstance(obj, np.integer):
        return int(obj)
    elif hasattr(np, 'floating') and isinstance(obj, np.floating):
        return float(obj)
    elif hasattr(np, 'ndarray') and isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(np, 'bool_') and isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {str(k): convert_to_json_serializable(v) for k, v in obj.items()}
    # Try to detect pandas Series or DataFrame
    elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict', None)):
        return convert_to_json_serializable(obj.to_dict())
    # Try to detect objects with __dict__ attribute
    elif hasattr(obj, '__dict__'):
        try:
            return convert_to_json_serializable(obj.__dict__)
        except:
            return str(obj)
    else:
        # For any other type, attempt string conversion as a fallback
        try:
            json.dumps(obj)
            return obj
        except:
            return str(obj)
