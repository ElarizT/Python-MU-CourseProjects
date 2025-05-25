"""
Data transformation routes for the Flask application.
These routes handle CSV and Excel file uploads and transformations using natural language instructions.
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, session
from werkzeug.utils import secure_filename
import os
import uuid
from functools import wraps
from datetime import datetime
from data_transformer import transform_dataframe

# Create a Blueprint for transform routes
transform_bp = Blueprint('transform', __name__)

# Helper: Import login_required decorator
def get_login_required():
    """Import login_required decorator from main app"""
    from app import login_required
    return login_required

# Main route for data transformation
@transform_bp.route('/', methods=['GET', 'POST'])
def transform_data():
    login_required = get_login_required()
    
    @login_required
    def protected_transform():
        if request.method == 'POST':
            # Check if the post request has the file part
            if 'file' not in request.files:
                return render_template('transform_data.html', error='No file part')
            
            file = request.files['file']
            
            # If user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                return render_template('transform_data.html', error='No selected file')
            
            # Check file extension
            allowed_extensions = {'csv', 'xlsx', 'xls'}
            file_ext = os.path.splitext(file.filename)[1][1:].lower()
            if file_ext not in allowed_extensions:
                return render_template('transform_data.html', 
                                    error=f'Unsupported file type. Please upload a CSV or Excel file.')
            
            # Get user instructions
            instructions = request.form.get('instructions', '')
            if not instructions.strip():
                return render_template('transform_data.html', 
                                    error='Please provide transformation instructions')
            
            try:
                # Save the uploaded file with a secure filename
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                
                # Transform the data using the instructions
                result = transform_dataframe(file_path, instructions, current_app.config)
                
                if not result['success']:
                    # If transformation failed, render the template with error
                    return render_template('transform_data.html', 
                                        error=result['error'],
                                        code=result.get('code'),
                                        instructions=instructions)
                
                # If successful, get the download URL
                download_url = url_for('download_file', 
                                    filename=result['transformed_filename'], 
                                    _external=True)
                
                # Render the result template
                return render_template('transform_result.html',
                                    download_url=download_url,
                                    original_filename=result['original_filename'],
                                    transformed_filename=result['transformed_filename'],
                                    code=result['code'],
                                    rows_before=result['rows_before'],
                                    rows_after=result['rows_after'], 
                                    columns_before=result['columns_before'],
                                    columns_after=result['columns_after'])
            
            except Exception as e:
                return render_template('transform_data.html', 
                                    error=f'Error processing file: {str(e)}',
                                    instructions=instructions)
        
        # GET request - render the upload form
        return render_template('transform_data.html')
    
    return protected_transform()

# Simplified route - direct to the transform page
@transform_bp.route('/transform_file', methods=['GET'])
def transform_file():
    login_required = get_login_required()
    
    @login_required
    def protected_transform_file():
        return redirect(url_for('transform.transform_data'))
    
    return protected_transform_file()
