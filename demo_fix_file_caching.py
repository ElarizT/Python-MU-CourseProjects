#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo script that simulates and fixes the issue with cached files
from previous uploads being used instead of new uploads.

This script will:
1. Simulate creation of a "cached" file (simulating previous upload)
2. Show how the system would incorrectly use this file
3. Demonstrate how to fix the issue using our new functions
"""

import os
import pandas as pd
import numpy as np
import tempfile
from file_optimizer import (
    read_csv_optimized, 
    clear_session_files,
    validate_csv_file,
    manage_uploaded_file,
    SESSION_FILES_DIR
)

def create_demo_files():
    """Create demo files for testing"""
    print("\n=== Creating demo files ===")
    
    # Create session directory if it doesn't exist
    if not os.path.exists(SESSION_FILES_DIR):
        os.makedirs(SESSION_FILES_DIR)
    
    # Create a "cached" file (simulating a file from a previous session)
    cached_file_path = os.path.join(SESSION_FILES_DIR, "azeri_text.txt")
    with open(cached_file_path, "w", encoding="utf-8") as f:
        f.write("""Azərbaycan dili, Azərbaycan türkcəsi və ya Azəri dili – Azərbaycan 
        Respublikasının rəsmi dili, həmçinin İranda və Gürcüstanda geniş yayılmış dildir. 
        Bu dil türk dilləri ailəsinin Oğuz qrupuna aiddir. 
        Azərbaycan dilində danışan 50 milyondan çox insan var ki, 
        bunların əksəriyyəti İran və Azərbaycanda yaşayır.""")
    print(f"Created cached file: {cached_file_path}")
    
    # Create a new CSV file (simulating a new upload)
    new_upload_path = os.path.join(tempfile.gettempdir(), "dataset_part1.csv")
    df = pd.DataFrame({
        "id": range(1, 101),
        "name": [f"Dataset Item {i}" for i in range(1, 101)],
        "value": np.random.rand(100) * 100,
        "category": np.random.choice(["A", "B", "C"], size=100)
    })
    df.to_csv(new_upload_path, index=False)
    print(f"Created new CSV file: {new_upload_path}")
    
    return cached_file_path, new_upload_path

def simulate_problem():
    """Simulate the problem of using cached files"""
    print("\n=== Simulating the problem ===")
    
    # In a system without proper file management:
    # When an upload happens, the system may incorrectly use a cached file
    
    # Let's list files in the session directory, which would simulate
    # what your system is currently doing - finding cached files
    print("Files in session directory:")
    for f in os.listdir(SESSION_FILES_DIR):
        print(f"- {f}")
    
    # Simulate reading the wrong file
    print("\nSimulating incorrect behavior (using cached file instead of new upload):")
    wrong_file_path = os.path.join(SESSION_FILES_DIR, "azeri_text.txt")
    
    try:
        with open(wrong_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"Read cached file instead of new upload: {wrong_file_path}")
            print(f"First 100 chars: {content[:100]}...")
            print("ERROR: Used cached file (azeri_text.txt) instead of the new CSV upload!")
    except Exception as e:
        print(f"Error: {e}")

def demonstrate_solution(new_file_path):
    """Demonstrate the solution using our new file management functions"""
    print("\n=== Demonstrating the solution ===")
    
    print("\nStep 1: Clear all cached files")
    result = clear_session_files()
    print(f"Clear result: {result}")
    
    print("\nStep 2: Process new upload correctly")
    # Read the file as bytes to simulate an upload
    with open(new_file_path, "rb") as f:
        file_bytes = f.read()
    
    # Process the "uploaded" file correctly
    upload_result = manage_uploaded_file(
        file_bytes, 
        filename=os.path.basename(new_file_path)
    )
    
    if upload_result["status"] != "success":
        print(f"Upload failed: {upload_result['message']}")
        return
    
    print(f"File uploaded successfully: {upload_result['filename']}")
    
    # Now process the CSV correctly
    content, metadata, is_truncated, full_size = read_csv_optimized(
        upload_result["file_path"]
    )
    
    print("\n=== Results ===")
    print(f"File processed: {metadata['filename']}")
    print(f"File size: {metadata['file_size_mb']:.2f} MB")
    print(f"Columns: {', '.join(metadata['column_names'])}")
    print(f"Sample rows: {metadata['num_rows_sampled']}")
    print(f"\nContent preview:\n{content[:500]}...")
    print("\nSuccess! Processed the correct CSV file instead of using cached files.")

def main():
    """Main function to demonstrate the issue and solution"""
    print("=== File Upload Caching Issue Demo ===")
    
    # Create demo files
    cached_file_path, new_upload_path = create_demo_files()
    
    # Simulate the problem
    simulate_problem()
    
    # Demonstrate the solution
    demonstrate_solution(new_upload_path)
    
    # Clean up
    print("\n=== Cleaning up ===")
    clear_session_files()
    if os.path.exists(new_upload_path):
        os.remove(new_upload_path)
    print("Cleanup complete")
    
    print("\n=== Summary ===")
    print("1. The issue was that your system was using cached files from previous uploads")
    print("2. The solution implemented clears cached files before processing new uploads")
    print("3. The new system also validates CSV files and properly manages upload sessions")
    print("\nNow you can handle multiple file uploads without conflicts!")

if __name__ == "__main__":
    main()
