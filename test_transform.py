"""
Test script for data transformation functionality.

This script tests the core data transformation functions
to ensure they work properly without the web interface.
"""

import os
import pandas as pd
import tempfile
from data_transformer import transform_dataframe, get_gemini_transform_code, safe_execute_code

def create_test_csv():
    """Create a simple CSV file for testing"""
    # Create a sample DataFrame
    data = {
        'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'Age': [25, 30, 35, 40, 45],
        'Salary': [50000, 60000, 70000, 80000, 90000],
        'Department': ['HR', 'IT', 'Finance', 'IT', 'Marketing']
    }
    df = pd.DataFrame(data)
    
    # Save to a temporary file
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, 'test_data.csv')
    df.to_csv(file_path, index=False)
    
    print(f"Created test CSV at: {file_path}")
    return file_path

def test_gemini_transform_code():
    """Test the Gemini API code generation function"""
    # Create a simple dataframe
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6]
    })
    
    # Get a preview string
    preview = f"DataFrame shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
    preview += f"Column names: {list(df.columns)}\n"
    preview += f"Column data types: {df.dtypes.to_dict()}\n\n"
    preview += "First 5 rows:\n"
    preview += df.head(5).to_string()
    
    # Test with a simple transformation instruction
    instructions = "Add a new column C that is the sum of columns A and B"
    
    print("\n--- Testing get_gemini_transform_code ---")
    code, error, token_usage = get_gemini_transform_code(instructions, preview)
    
    if error:
        print(f"ERROR: {error}")
    else:
        print(f"Generated code: \n{code}")
        print(f"Token usage: {token_usage}")
    
    return code, token_usage

def test_safe_execute_code(code):
    """Test the safe code execution function"""
    # Create a simple dataframe
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6]
    })
    
    print("\n--- Testing safe_execute_code ---")
    result_df, error = safe_execute_code(code, df)
    
    if error:
        print(f"ERROR: {error}")
    else:
        print("Code executed successfully")
        print(result_df)
    
    return result_df

def test_full_transform_flow():
    """Test the complete transformation flow"""
    # Create a test file
    file_path = create_test_csv()
    
    # Define a simple transformation
    instructions = "Filter rows where Age > 30 and calculate the average salary by department"
    
    # Mock app_config
    app_config = {'UPLOAD_FOLDER': tempfile.gettempdir()}
    
    print("\n--- Testing full transform flow ---")
    result = transform_dataframe(file_path, instructions, app_config)
    
    if result.get('success'):
        print("Transformation successful!")
        print(f"Original rows: {result['rows_before']}, Transformed rows: {result['rows_after']}")
        print(f"Token usage: {result.get('token_usage', 'N/A')}")
        print(f"Result file: {result['result_path']}")
        
        # Try to read the result file
        if os.path.exists(result['result_path']):
            result_df = pd.read_excel(result['result_path'])
            print("\nResult DataFrame:")
            print(result_df)
    else:
        print(f"ERROR: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    print("Running data transformation tests...")
    
    # Test Gemini code generation
    code, token_usage = test_gemini_transform_code()
    
    # Test safe code execution
    if code:
        result_df = test_safe_execute_code(code)
    
    # Test full transformation flow
    result = test_full_transform_flow()
    
    print("\nAll tests completed.")
