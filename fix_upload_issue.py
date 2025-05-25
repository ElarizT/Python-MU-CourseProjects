#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example showing how to fix the file caching issue with uploaded CSV files

This script demonstrates how to clear previously cached files and ensure
that new uploads are correctly processed.
"""

import os
import sys
import pandas as pd
from file_optimizer import clear_session_files, manage_uploaded_file, read_csv_optimized

def fix_file_upload_issue(csv_file_path):
    """
    Fix the issue where a previously cached file (like azeri_text.txt) is used
    instead of a newly uploaded CSV file.
    
    Args:
        csv_file_path (str): Path to the CSV file to process
        
    Returns:
        dict: Results of the operation
    """
    print("\n=== FIXING FILE UPLOAD CACHING ISSUE ===")
    
    # Step 1: Clear any previous cached files
    print("\nStep 1: Clear all cached session files")
    clear_result = clear_session_files()
    print(f"Clear result: {clear_result}")
    
    # Step 2: Handle the new file upload
    print("\nStep 2: Process the new CSV upload")
    with open(csv_file_path, 'rb') as f:
        file_bytes = f.read()
    
    upload_result = manage_uploaded_file(
        file_bytes, 
        filename=os.path.basename(csv_file_path)
    )
    
    if upload_result["status"] != "success":
        print(f"Upload failed: {upload_result['message']}")
        return upload_result
    
    print(f"File uploaded successfully: {upload_result['filename']}")
    
    # Step 3: Process the uploaded CSV
    print("\nStep 3: Process the uploaded CSV file")
    content, metadata, is_truncated, full_size = read_csv_optimized(
        upload_result["file_path"],
        validate_first=True
    )
    
    # Display results
    print("\n=== RESULTS ===")
    print(f"File processed: {metadata['filename']}")
    print(f"File size: {metadata['file_size_mb']:.2f} MB")
    print(f"Columns: {', '.join(metadata['column_names'])}")
    print(f"Sample rows: {metadata['num_rows_sampled']}")
    print(f"Content length: {len(content)} characters")
    print(f"Content preview: {content[:200]}...")
    
    return {
        "status": "success",
        "upload_result": upload_result,
        "metadata": metadata,
        "content_preview": content[:500]
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_upload_issue.py <path_to_csv_file>")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    
    if not os.path.exists(csv_file_path):
        print(f"Error: File not found - {csv_file_path}")
        sys.exit(1)
    
    result = fix_file_upload_issue(csv_file_path)
    
    # Print final status
    print(f"\nOperation completed with status: {result['status']}")
