#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to verify the fix for content mismatch issue when removing columns
"""

import os
import sys
import pandas as pd
import tempfile
from excel_data_processor import process_csv_file, get_file_info

def test_content_preservation():
    """Test that original data content is preserved when removing columns"""
    # Create a test file with SpaceX launch data
    test_file_path = os.path.join(tempfile.gettempdir(), "spacex_test.csv")
    with open(test_file_path, "w") as f:
        f.write("FlightNumber,Date,BoosterVersion,PayloadMass,Orbit,LaunchSite\n")
        f.write("1,2010-06-04,Falcon 9,6104.959412,LEO,CCAFS SLC 40\n")
        f.write("2,2012-05-22,Falcon 9,525.000000,LEO,CCAFS SLC 40\n")
        f.write("3,2013-03-01,Falcon 9,677.000000,ISS,CCAFS SLC 40\n")
    
    print(f"Created test file: {test_file_path}")
    
    # Print original content
    print("\nOriginal file content:")
    df_original = pd.read_csv(test_file_path)
    print(df_original)
    
    # Process file to remove Orbit column
    result = process_csv_file(
        test_file_path,
        operations={"remove_columns": ["Orbit"]}
    )
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return False
    
    # Print processed content
    print("\nProcessed file content (after removing Orbit):")
    df_processed = pd.read_csv(result["processed_file"])
    print(df_processed)
    
    # Verify that original data is preserved except for the removed column
    # Check row count
    if len(df_original) != len(df_processed):
        print(f"Error: Row count mismatch! Original: {len(df_original)}, Processed: {len(df_processed)}")
        return False
    
    # Check columns (should have one less)
    expected_columns = [col for col in df_original.columns if col != "Orbit"]
    if list(df_processed.columns) != expected_columns:
        print(f"Error: Column mismatch! Expected: {expected_columns}, Got: {list(df_processed.columns)}")
        return False
    
    # Check data values for a sample column
    if not all(df_original["FlightNumber"] == df_processed["FlightNumber"]):
        print("Error: Data values mismatch in FlightNumber column!")
        return False
    
    # Check date column
    if not all(df_original["Date"] == df_processed["Date"]):
        print("Error: Data values mismatch in Date column!")
        return False
    
    print("\nSuccess! Original data content was preserved correctly while removing the Orbit column.")
    return True

if __name__ == "__main__":
    success = test_content_preservation()
    sys.exit(0 if success else 1)
