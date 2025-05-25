#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CSV and large file optimizer for LightYearAI

This script improves the handling of large CSV and Excel files
by implementing better sampling, timeout handling, and response 
size limiting strategies.
"""

import os
import pandas as pd
import io
import numpy as np
from datetime import datetime
import glob
import shutil

# Make functions available at the module level
__all__ = ['convert_to_serializable', 'read_csv_optimized', 'clear_session_files', 'clear_flask_session_data', 'clear_all_session_data', 'aggressive_session_clear', 'validate_csv_file', 'manage_uploaded_file']

# Add a session directory constant - adjust this path as needed
SESSION_FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_files")

def clear_session_files(file_pattern=None):
    """
    Clear cached files from previous sessions
    
    Args:
        file_pattern (str, optional): Specific pattern to match files for deletion
        
    Returns:
        dict: Result of the cleanup operation
    """
    try:
        # Create session directory if it doesn't exist
        if not os.path.exists(SESSION_FILES_DIR):
            os.makedirs(SESSION_FILES_DIR)
            return {"status": "success", "message": "Session directory created, no files to clear"}
        
        # Pattern for files to remove
        pattern = os.path.join(SESSION_FILES_DIR, file_pattern if file_pattern else "*.*")
        
        # Find files matching pattern
        files_to_remove = glob.glob(pattern)
        count = len(files_to_remove)
        
        # Remove each file
        for file_path in files_to_remove:
            try:
                os.remove(file_path)
                print(f"[FILE OPTIMIZER] Removed cached file: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"[FILE OPTIMIZER] Error removing {file_path}: {e}")
        
        return {
            "status": "success", 
            "message": f"Cleared {count} session files",
            "files_removed": count
        }
    
    except Exception as e:
        print(f"[FILE OPTIMIZER] Error clearing session files: {e}")
        return {"status": "error", "message": f"Error clearing session files: {str(e)}"}

def validate_csv_file(file_path):
    """
    Validate that a file is a properly formatted CSV
    
    Args:
        file_path (str): Path to the file to validate
        
    Returns:
        dict: Validation result with status and message
    """
    try:
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in ['.csv', '.txt']:
            return {"valid": False, "message": f"Invalid file type: {ext}. Only CSV files are supported."}
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {"valid": False, "message": f"File not found: {file_path}"}
        
        # Try to read the first row to validate CSV format
        try:
            df_sample = pd.read_csv(file_path, nrows=1)
            
            # Check for consistent number of columns
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip() if f.readline() else ""
            
            if second_line:
                first_line_fields = first_line.count(',') + 1
                second_line_fields = second_line.count(',') + 1
                
                if first_line_fields != second_line_fields:
                    return {"valid": False, "message": f"Inconsistent number of columns: header has {first_line_fields} fields, data has {second_line_fields} fields"}
        
        except pd.errors.ParserError as e:
            return {"valid": False, "message": f"CSV parsing error: {str(e)}"}
        
        # If we get here, the file is valid
        return {"valid": True, "message": "File validation successful"}
    
    except pd.errors.EmptyDataError:
        # File exists but is empty
        return {"valid": False, "message": "The CSV file is empty"}
    
    except Exception as e:
        # Other errors
        return {"valid": False, "message": f"Validation error: {str(e)}"}

def manage_uploaded_file(uploaded_file, filename=None, clear_previous=True):
    """
    Manage uploaded file by saving it to session directory and clearing previous files if needed
    
    Args:
        uploaded_file: The uploaded file object (bytes or file-like object)
        filename (str, optional): Name to save the file as
        clear_previous (bool): Whether to clear previous session files
        
    Returns:
        dict: Result containing file path and status
    """
    try:
        # Create session directory if it doesn't exist
        if not os.path.exists(SESSION_FILES_DIR):
            os.makedirs(SESSION_FILES_DIR)
        
        # Clear previous files if requested
        if clear_previous:
            clear_session_files()
        
        # Generate filename if not provided
        if not filename:
            filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Clean the filename to be safe
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(SESSION_FILES_DIR, safe_filename)
        
        # Save the uploaded file
        if hasattr(uploaded_file, 'read'):
            # If it's a file-like object
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.read())
        elif isinstance(uploaded_file, bytes):
            # If it's bytes
            with open(file_path, 'wb') as f:
                f.write(uploaded_file)
        else:
            return {"status": "error", "message": "Unsupported file object type"}
        
        print(f"[FILE OPTIMIZER] Saved uploaded file to: {file_path}")
        
        # Validate the saved file
        validation = validate_csv_file(file_path)
        if not validation["valid"]:
            # Remove invalid file
            os.remove(file_path)
            return {"status": "error", "message": validation["message"]}
        
        return {
            "status": "success",
            "file_path": file_path,
            "filename": safe_filename,
            "message": f"File successfully uploaded and saved as {safe_filename}"
        }
        
    except Exception as e:
        print(f"[FILE OPTIMIZER] Error managing uploaded file: {e}")
        return {"status": "error", "message": f"Error managing upload: {str(e)}"}

def convert_to_serializable(obj):
    """
    Convert NumPy types and other non-serializable objects to JSON-serializable types.
    
    Args:
        obj: Any Python object
        
    Returns:
        A JSON-serializable version of the object
    """
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj) 
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, dict):
        return {str(k): convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [convert_to_serializable(i) for i in obj]
    else:
        return obj

def read_csv_optimized(file_path, max_size_mb=5, sample_rows=1000, validate_first=True):
    """
    Optimized CSV reader with intelligent sampling for large files
    
    Args:
        file_path (str): Path to the CSV file
        max_size_mb (int): Maximum file size in MB before sampling
        sample_rows (int): Number of rows to sample for large files
        validate_first (bool): Whether to validate the file before reading
        
    Returns:
        tuple: (text_content, metadata, is_truncated, full_content_size)
    """
    print(f"[CSV OPTIMIZER] Reading file: {file_path}")
    start_time = datetime.now()
    
    # Validate the file if requested
    if validate_first:
        validation = validate_csv_file(file_path)
        if not validation["valid"]:
            error_message = f"CSV validation failed: {validation['message']}"
            return error_message, {"error": validation["message"]}, False, len(error_message)
    
    # Get file size
    try:
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"[CSV OPTIMIZER] File size: {file_size_mb:.2f} MB")
    except FileNotFoundError:
        error_message = f"File not found: {file_path}"
        return error_message, {"error": error_message}, False, len(error_message)
    
    # Track if content is truncated
    is_truncated = False
    full_content_size = 0
    
    try:
        # For large files, use sampling
        if file_size_mb > max_size_mb:
            print(f"[CSV OPTIMIZER] Large file detected, using sampling strategy")
            is_truncated = True
            
            # First get column names and data types
            df_header = pd.read_csv(file_path, nrows=1)
            num_columns = len(df_header.columns)
            print(f"[CSV OPTIMIZER] File has {num_columns} columns")
            
            # Get first sample_rows/2 rows
            df_start = pd.read_csv(file_path, nrows=sample_rows//2)
            print(f"[CSV OPTIMIZER] Read {len(df_start)} rows from beginning")
            
            # Calculate approximate total rows
            approx_row_size = file_size / (len(df_start) or 1) / (num_columns or 1)
            approx_total_rows = int(file_size / approx_row_size)
            print(f"[CSV OPTIMIZER] Estimated total rows: ~{approx_total_rows:,}")
            
            # Try to get some rows from the end
            try:
                # Skip to near the end and get sample_rows/2 more rows
                if approx_total_rows > sample_rows:
                    skip_to = approx_total_rows - sample_rows//2
                    print(f"[CSV OPTIMIZER] Attempting to read {sample_rows//2} rows starting at row {skip_to:,}")
                    df_end = pd.read_csv(file_path, skiprows=range(1, skip_to), nrows=sample_rows//2)
                    print(f"[CSV OPTIMIZER] Successfully read {len(df_end)} rows from end")
                    
                    # Combine for full sample
                    df = pd.concat([df_start, df_end])
                    sample_note = f"\n\n[Note: This is a sample of {len(df)} rows from a large CSV with approximately {approx_total_rows:,} total rows]"
                else:
                    # If file isn't that large, just use the beginning sample
                    df = df_start
                    sample_note = f"\n\n[Note: This is a sample of {len(df)} rows from the CSV file]"
            except Exception as e:
                print(f"[CSV OPTIMIZER] Error reading end sample: {e}")
                df = df_start
                sample_note = f"\n\n[Note: This is a sample of {len(df)} rows from the beginning of a large CSV with approximately {approx_total_rows:,} total rows]"
        else:
            # For smaller files, read everything
            print(f"[CSV OPTIMIZER] File is under size threshold, reading entirely")
            df = pd.read_csv(file_path)
            sample_note = ""
              # Generate metadata about the file - ensure all values are JSON serializable
        metadata = {
            "filename": os.path.basename(file_path),
            "file_size_bytes": int(file_size),
            "file_size_mb": float(file_size_mb),
            "num_columns": int(len(df.columns)),
            "column_names": [str(col) for col in df.columns],
            "num_rows_sampled": int(len(df)),
            "is_truncated": bool(is_truncated),
        }
        
        # Add statistics if appropriate
        if len(df) > 0:            # Get basic statistics for numeric columns
            numeric_stats = {}
            for col in df.select_dtypes(include=['number']).columns:
                try:
                    # Convert NumPy types to standard Python types for JSON serialization
                    numeric_stats[col] = {
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "mean": float(df[col].mean()),
                        "median": float(df[col].median())
                    }
                except:
                    pass
            
            metadata["numeric_stats"] = numeric_stats
            
            # Get value counts for categorical columns with few unique values
            categorical_stats = {}
            for col in df.select_dtypes(include=['object', 'category']).columns:
                try:
                    unique_values = df[col].nunique()
                    if unique_values <= 10:  # Only include columns with 10 or fewer unique values                        # Convert NumPy types to standard Python types for JSON serialization
                        value_counts = df[col].value_counts().head(10)
                        categorical_stats[col] = {str(k): int(v) for k, v in value_counts.items()}
                except:
                    pass
                    
            metadata["categorical_stats"] = categorical_stats
        
        # Convert to string representation
        buffer = io.StringIO()
        
        # Create a header with metadata
        header = f"CSV File Analysis:\n"
        header += f"- Filename: {os.path.basename(file_path)}\n"
        header += f"- Size: {file_size:,} bytes ({file_size_mb:.2f} MB)\n"
        header += f"- Columns ({len(df.columns)}): {', '.join(df.columns.tolist())}\n"
        
        # Add numeric column statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            header += f"- Numeric column statistics:\n"
            for col in list(numeric_cols)[:5]:  # Limit to first 5 numeric columns
                try:
                    header += f"  * {col}: min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}\n"
                except:
                    pass
            if len(numeric_cols) > 5:
                header += f"  * (statistics for {len(numeric_cols)-5} more numeric columns not shown)\n"
        
        buffer.write(header + "\n\nData Sample:\n")
        
        # Write the data representation
        df.to_string(buffer, index=False)
        buffer.write(sample_note)
        
        # Get the result
        content = buffer.getvalue()
        full_content_size = len(content)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"[CSV OPTIMIZER] Processing completed in {duration:.2f} seconds")
        print(f"[CSV OPTIMIZER] Content length: {len(content)} characters")
        
        # Final check to ensure all metadata is JSON-serializable
        serializable_metadata = convert_to_serializable(metadata)
        
        return content, serializable_metadata, is_truncated, full_content_size
        
    except Exception as e:
        print(f"[CSV OPTIMIZER] Error processing file: {e}")
        error_message = f"Error processing CSV file: {str(e)}"
        return error_message, {"error": str(e)}, False, len(error_message)

def clear_flask_session_data(flask_session):
    """
    Clear Flask session data related to uploaded files with robust clearing methods
    
    Args:
        flask_session: The Flask session object
        
    Returns:
        dict: Result of the session clearing operation
    """
    try:
        cleared_files = []
        
        # Method 1: Standard deletion
        if 'current_file' in flask_session:
            old_filename = flask_session['current_file'].get('filename', 'unknown')
            print(f"[SESSION CLEAR] Removing old file data: {old_filename}")
            cleared_files.append(old_filename)
            del flask_session['current_file']
        
        # Method 2: Explicit pop (backup method)
        popped_file = flask_session.pop('current_file', None)
        if popped_file and popped_file.get('filename') not in cleared_files:
            print(f"[SESSION CLEAR] Popped additional file data: {popped_file.get('filename', 'unknown')}")
            cleared_files.append(popped_file.get('filename', 'unknown'))
        
        # Method 3: Clear any other file-related session keys
        file_related_keys = [key for key in flask_session.keys() if 'file' in key.lower()]
        for key in file_related_keys:
            if key not in ['current_file']:  # Already handled above
                print(f"[SESSION CLEAR] Removing file-related key: {key}")
                flask_session.pop(key, None)
        
        # Force session modification
        flask_session.modified = True
        flask_session.permanent = True  # Ensure session persistence settings
        
        if cleared_files:
            return {
                "status": "success", 
                "message": f"Cleared Flask session data for: {', '.join(cleared_files)}",
                "cleared_file": cleared_files[0] if len(cleared_files) == 1 else cleared_files
            }
        else:
            return {
                "status": "success", 
                "message": "No current_file in Flask session to clear",
                "cleared_file": None
            }
    except Exception as e:
        print(f"[SESSION CLEAR] Error clearing Flask session data: {e}")
        return {"status": "error", "message": f"Error clearing Flask session data: {str(e)}"}

def clear_all_session_data(flask_session, file_pattern=None):
    """
    Clear both physical session files and Flask session data
    
    Args:
        flask_session: The Flask session object
        file_pattern (str, optional): Specific pattern to match files for deletion
        
    Returns:
        dict: Combined result of both clearing operations
    """
    try:
        # Clear physical files
        file_result = clear_session_files(file_pattern)
        
        # Clear Flask session data
        session_result = clear_flask_session_data(flask_session)
        
        return {
            "status": "success",
            "message": f"Cleared both session files and Flask data",
            "file_clearing": file_result,
            "session_clearing": session_result
        }
    except Exception as e:
        print(f"[SESSION CLEAR] Error in clear_all_session_data: {e}")
        return {"status": "error", "message": f"Error clearing all session data: {str(e)}"}

def aggressive_session_clear(flask_session):
    """
    Aggressively clear ALL file-related session data with multiple strategies
    Use this for troubleshooting persistent session data issues
    
    Args:
        flask_session: The Flask session object
        
    Returns:
        dict: Result of the aggressive clearing operation
    """
    try:
        print("[AGGRESSIVE CLEAR] Starting comprehensive session clearing...")
        cleared_data = []
        
        # Step 1: Log current session state
        session_keys = list(flask_session.keys())
        print(f"[AGGRESSIVE CLEAR] Current session keys: {session_keys}")
        
        # Step 2: Clear all file-related data
        for key in session_keys:
            if 'file' in key.lower() or 'upload' in key.lower() or 'current' in key.lower():
                value = flask_session.pop(key, None)
                if value:
                    if isinstance(value, dict) and 'filename' in value:
                        cleared_data.append(f"{key}: {value.get('filename')}")
                    else:
                        cleared_data.append(f"{key}: {type(value).__name__}")
                    print(f"[AGGRESSIVE CLEAR] Removed {key}")
        
        # Step 3: Specifically target 'current_file' with multiple methods
        current_file_cleared = False
        
        # Method A: Direct deletion
        if 'current_file' in flask_session:
            old_file = flask_session['current_file']
            del flask_session['current_file']
            print(f"[AGGRESSIVE CLEAR] Deleted current_file: {old_file.get('filename', 'unknown')}")
            current_file_cleared = True
        
        # Method B: Pop with None default
        popped = flask_session.pop('current_file', None)
        if popped:
            print(f"[AGGRESSIVE CLEAR] Popped remaining current_file: {popped.get('filename', 'unknown')}")
            current_file_cleared = True
        
        # Method C: Set to None and then delete
        flask_session['current_file'] = None
        flask_session.pop('current_file', None)
        
        # Step 4: Force session changes
        flask_session.modified = True
        flask_session.permanent = True
        
        # Step 5: Verify clearing
        remaining_keys = [k for k in flask_session.keys() if 'file' in k.lower()]
        if remaining_keys:
            print(f"[AGGRESSIVE CLEAR] WARNING: File-related keys still present: {remaining_keys}")
        else:
            print(f"[AGGRESSIVE CLEAR] SUCCESS: All file-related data cleared")
            
        return {
            "status": "success",
            "message": f"Aggressively cleared session data",
            "cleared_data": cleared_data,
            "current_file_cleared": current_file_cleared,
            "remaining_file_keys": remaining_keys
        }
        
    except Exception as e:
        print(f"[AGGRESSIVE CLEAR] Error during aggressive clearing: {e}")
        return {
            "status": "error",
            "message": f"Error during aggressive session clearing: {str(e)}"
        }
