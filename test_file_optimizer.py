#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Unit tests for the file_optimizer module
"""

import os
import sys
import unittest
import tempfile
import pandas as pd
import numpy as np
import shutil
from io import StringIO

# Import the module
from file_optimizer import (
    convert_to_serializable, 
    read_csv_optimized, 
    clear_session_files,
    validate_csv_file,
    manage_uploaded_file,
    SESSION_FILES_DIR
)

class TestFileOptimizer(unittest.TestCase):
    """Test cases for file_optimizer module functions"""
    
    def setUp(self):
        """Create test files and directory"""
        # Create test directory if it doesn't exist
        if not os.path.exists(SESSION_FILES_DIR):
            os.makedirs(SESSION_FILES_DIR)
            
        # Create a test CSV file
        self.test_csv_path = os.path.join(tempfile.gettempdir(), "test_file_optimizer.csv")
        df = pd.DataFrame({
            'id': range(1, 101),
            'name': [f"Item {i}" for i in range(1, 101)],
            'value': np.random.rand(100) * 100
        })
        df.to_csv(self.test_csv_path, index=False)
        
        # Create an invalid CSV file with inconsistent columns
        self.invalid_csv_path = os.path.join(tempfile.gettempdir(), "invalid_test.csv")
        with open(self.invalid_csv_path, 'w') as f:
            f.write("col1,col2,col3\nvalue1,value2\nvalue3,value4,value5,value6")
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
        if os.path.exists(self.invalid_csv_path):
            os.remove(self.invalid_csv_path)
            
        # Clear session files
        clear_session_files()
    
    def test_clear_session_files(self):
        """Test clearing session files"""
        # Create some test files in session dir
        for i in range(3):
            with open(os.path.join(SESSION_FILES_DIR, f"test_{i}.txt"), 'w') as f:
                f.write("Test content")
        
        # Clear the files
        result = clear_session_files()
        
        # Check that files were cleared
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(os.listdir(SESSION_FILES_DIR)), 0)
    
    def test_validate_csv_file(self):
        """Test CSV file validation"""
        # Test with valid CSV
        valid_result = validate_csv_file(self.test_csv_path)
        self.assertTrue(valid_result["valid"])
        
        # Test with invalid CSV
        invalid_result = validate_csv_file(self.invalid_csv_path)
        self.assertFalse(invalid_result["valid"])
        
        # Test with non-existent file
        not_found_result = validate_csv_file("this_file_does_not_exist.csv")
        self.assertFalse(not_found_result["valid"])
    
    def test_manage_uploaded_file(self):
        """Test file upload management"""
        # Read test file as bytes
        with open(self.test_csv_path, 'rb') as f:
            file_bytes = f.read()
        
        # Test upload with bytes
        result = manage_uploaded_file(file_bytes, "test_upload.csv")
        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(result["file_path"]))
        
        # Verify clear previous works
        second_result = manage_uploaded_file(file_bytes, "another_test.csv", clear_previous=True)
        self.assertEqual(second_result["status"], "success")
        # Original file should be gone
        self.assertFalse(os.path.exists(result["file_path"]))
        # New file should exist
        self.assertTrue(os.path.exists(second_result["file_path"]))
    
    def test_read_csv_optimized(self):
        """Test optimized CSV reading"""
        # Test with valid file
        content, metadata, is_truncated, full_size = read_csv_optimized(self.test_csv_path)
        self.assertIsInstance(content, str)
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata["num_columns"], 3)  # id, name, value
        self.assertEqual(metadata["num_rows_sampled"], 100)
        
        # Test with validation on invalid file
        content, metadata, is_truncated, full_size = read_csv_optimized(
            self.invalid_csv_path, validate_first=True
        )
        # The error message could vary, but should contain error info
        self.assertIn("error", metadata)

if __name__ == "__main__":
    unittest.main()
