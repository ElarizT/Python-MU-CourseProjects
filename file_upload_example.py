#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example script demonstrating how to use the file_optimizer module
for handling file uploads and clearing cached files.

Usage:
    python file_upload_example.py
"""

import os
import pandas as pd
from file_optimizer import (
    read_csv_optimized, 
    clear_session_files, 
    validate_csv_file, 
    manage_uploaded_file
)

def simulate_file_upload(file_path, new_filename=None):
    """
    Simulates uploading a file and processing it
    
    Args:
        file_path (str): Path to the local file to "upload"
        new_filename (str, optional): Name to save the file as
        
    Returns:
        dict: Result of the operation
    """
    try:
        print(f"[EXAMPLE] Simulating upload of: {file_path}")
        
        # First clear any cached files from previous sessions
        clear_result = clear_session_files()
        print(f"[EXAMPLE] Clear session result: {clear_result}")
        
        # Read the file into bytes (simulating an upload)
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        
        # Process the uploaded file
        upload_result = manage_uploaded_file(
            file_bytes,
            filename=new_filename or os.path.basename(file_path),
            clear_previous=True
        )
        
        if upload_result["status"] != "success":
            print(f"[EXAMPLE] Upload failed: {upload_result['message']}")
            return upload_result
        
        # Now read the managed file
        file_path = upload_result["file_path"]
        print(f"[EXAMPLE] Processing uploaded file: {file_path}")
        
        # Process the CSV file
        content, metadata, is_truncated, full_size = read_csv_optimized(
            file_path,
            max_size_mb=5,
            sample_rows=1000
        )
        
        # Display results summary
        print(f"[EXAMPLE] File processed successfully")
        print(f"[EXAMPLE] Content length: {len(content)} chars")
        print(f"[EXAMPLE] Is truncated: {is_truncated}")
        print(f"[EXAMPLE] Number of columns: {metadata['num_columns']}")
        print(f"[EXAMPLE] Sample rows: {metadata['num_rows_sampled']}")
        
        return {
            "status": "success",
            "upload_result": upload_result,
            "metadata": metadata,
            "content_preview": content[:500] + "..." if len(content) > 500 else content
        }
        
    except Exception as e:
        print(f"[EXAMPLE] Error: {e}")
        return {"status": "error", "message": str(e)}

def example_usage():
    """Example usage of the file_optimizer module"""
    # 1. Clear all cached files first
    print("\n=== CLEARING SESSION FILES ===")
    clear_result = clear_session_files()
    print(f"Clear result: {clear_result}")
    
    # 2. Demonstrate validation of a file
    print("\n=== VALIDATING A CSV FILE ===")
    # Replace with a path to your actual CSV file
    csv_path = input("Enter path to a CSV file to validate: ")
    validation_result = validate_csv_file(csv_path)
    print(f"Validation result: {validation_result}")
    
    # 3. Process a CSV file
    if validation_result["valid"]:
        print("\n=== PROCESSING CSV FILE ===")
        result = simulate_file_upload(csv_path)
        print("\nOperation result summary:")
        print(f"Status: {result['status']}")
        if result["status"] == "success":
            print(f"File: {result['upload_result']['filename']}")
            print(f"Content preview:\n{result['content_preview']}")
    
    print("\n=== FINISHED ===")

if __name__ == "__main__":
    example_usage()
