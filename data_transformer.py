"""
Data Transformation Module

This module provides functionality to transform CSV and Excel files based on natural language
instructions interpreted by the Gemini API.
"""

import os
import uuid
import pandas as pd
import traceback
import re
import json
from datetime import datetime
import google.generativeai as genai
from flask import url_for

# Safe execution environment for user code
def safe_execute_code(code_string, dataframe):
    """
    Safely execute generated pandas code on the provided dataframe
    
    Args:
        code_string (str): The Python code with Pandas transformations
        dataframe (pd.DataFrame): The input DataFrame to transform
    
    Returns:
        tuple: (transformed_df, error_message)
    """
    # Create a copy of the input dataframe to avoid side effects
    try:
        # Use a copy of the input dataframe
        df = dataframe.copy()
        
        # Set up a restricted globals dictionary with only safe modules
        safe_globals = {
            'pd': pd,
            'df': df,
            'DataFrame': pd.DataFrame,
            'Series': pd.Series,
            'np': __import__('numpy'),
            're': re,
            'datetime': datetime
        }
        
        # Execute the code in the safe environment
        exec(code_string, safe_globals)
        
        # Get the transformed dataframe from the safe environment
        result_df = safe_globals['df']
        
        # Validation: make sure the result is actually a DataFrame
        if not isinstance(result_df, pd.DataFrame):
            return None, "The executed code did not produce a valid DataFrame."
        
        return result_df, None
    except Exception as e:
        error_details = traceback.format_exc()
        error_message = f"Error executing transformation code: {str(e)}\n\n{error_details}"
        return None, error_message


def get_gemini_transform_code(prompt, df_preview):
    """
    Use Gemini API to generate pandas transformation code based on a prompt
    
    Args:
        prompt (str): User's natural language instruction for data transformation
        df_preview (str): String representation of the DataFrame preview
    
    Returns:
        tuple: (code, error_message, token_count)
    """
    try:
        # Get Gemini model
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Create system prompt with instructions
        system_prompt = """
        You are a data transformation assistant specialized in writing Python code using pandas.
        Your task is to generate Python code that transforms a DataFrame based on natural language instructions.
        
        Guidelines:
        1. Only output valid Python code that uses pandas to transform the input DataFrame.
        2. Always use the variable 'df' as the input and output DataFrame.
        3. Include clear comments in your code explaining what each part does.
        4. Do not include markdown code blocks or any text outside the code itself.
        5. Do not include any print statements or visualizations.
        6. Do not import any additional packages that might not be available.
        7. Use safe, efficient pandas operations.
        8. If the instructions are unclear, make reasonable assumptions and document them in code comments.
        9. For complex transformations, break the process into smaller steps with clear comments.
        10. Return ONLY the executable Python code without any explanations or markdown formatting.
        """
        
        # Create user prompt with instructions and data
        user_prompt = f"""
        Here is a preview of the DataFrame:
        
        ```
        {df_preview}
        ```
        
        Please write Python code using pandas to transform this DataFrame according to these instructions:
        
        {prompt}
        
        Return only the executable Python code without any explanations or markdown formatting.
        """
        
        # Generate response from Gemini
        response = model.generate_content(
            [system_prompt, user_prompt],
            generation_config={
                "temperature": 0.2,  # Lower temperature for more deterministic code generation
                "max_output_tokens": 2048
            }
        )
        
        code = response.text
        
        # Clean up the code to remove any markdown formatting that might remain
        code = code.replace("```python", "").replace("```", "").strip()
          # Get token usage if available
        token_usage = 0
        
        # Try multiple ways to extract token usage
        try:
            # Method 1: Check candidates attribute
            if hasattr(response, 'candidates') and len(response.candidates) > 0:
                if hasattr(response.candidates[0], 'token_count'):
                    token_usage = response.candidates[0].token_count
                    
            # Method 2: Check usage_metadata
            elif hasattr(response, 'usage_metadata'):
                token_usage = response.usage_metadata.total_token_count
                
            # Method 3: Estimate tokens from input and output length if no token count available
            if token_usage == 0:
                # Rough estimation
                prompt_tokens = len(df_preview) // 4
                code_tokens = len(code) // 4
                token_usage = prompt_tokens + code_tokens
            
            # Validate token_usage is an integer
            token_usage = int(token_usage)
        except Exception as token_err:
            print(f"Error getting token usage: {token_err}")
            # Fallback to estimation
            token_usage = (len(df_preview) + len(code)) // 4
        
        return code, None, token_usage
    except Exception as e:
        error_details = traceback.format_exc()
        error_message = f"Error generating transformation code: {str(e)}\n\n{error_details}"
        return None, error_message, 0


def transform_dataframe(file_path, instructions, app_config):
    """
    Transform a CSV or Excel file based on natural language instructions
    
    Args:
        file_path (str): Path to the file to transform
        instructions (str): Natural language instructions for transformation
        app_config (dict): Flask app configuration
    
    Returns:
        dict: Result object with success/error status and file path if successful
    """
    try:
        from file_utils import read_dataframe_from_file
        
        # Read the file into a DataFrame
        df = read_dataframe_from_file(file_path)
        
        # Get a preview of the DataFrame (first few rows + column info)
        preview = f"DataFrame shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
        preview += f"Column names: {list(df.columns)}\n"
        preview += f"Column data types: {df.dtypes.to_dict()}\n\n"
        preview += "First 5 rows:\n"
        preview += df.head(5).to_string()
        
        # Get transformation code from Gemini
        code, error, token_usage = get_gemini_transform_code(instructions, preview)
        if error:
            return {"success": False, "error": error}
        
        # Execute the code safely
        result_df, exec_error = safe_execute_code(code, df)
        if exec_error:
            return {"success": False, "error": exec_error, "code": code}
        
        # Create a unique filename for the result
        original_filename = os.path.basename(file_path)
        base_name, _ = os.path.splitext(original_filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"{base_name}_transformed_{timestamp}.xlsx"
        result_path = os.path.join(app_config['UPLOAD_FOLDER'], result_filename)
        
        # Save the transformed DataFrame as Excel
        result_df.to_excel(result_path, index=False)
        
        return {
            "success": True,
            "original_filename": original_filename,
            "transformed_filename": result_filename,
            "result_path": result_path,
            "code": code,
            "rows_before": df.shape[0],
            "rows_after": result_df.shape[0],
            "columns_before": df.shape[1],
            "columns_after": result_df.shape[1],
            "token_usage": token_usage
        }
    
    except Exception as e:
        error_details = traceback.format_exc()
        error_message = f"Error transforming data: {str(e)}\n\n{error_details}"
        return {"success": False, "error": error_message}