#!/usr/bin/env python3
"""
Simple test server for CrewAI integration
This bypasses the full app initialization to test just the CrewAI functionality
"""

from flask import Flask, request, jsonify
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

app = Flask(__name__)

@app.route('/')
def home():
    return "CrewAI Test Server is running!"

@app.route('/test_crew_excel', methods=['POST'])
def test_crew_excel():
    """Test endpoint for CrewAI Excel generation"""
    try:
        # Get the prompt from the request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
            
        prompt = data.get('prompt', 'Generate a simple sales report with monthly data for 2024')
        
        print(f"Received prompt: {prompt}")
          # Import CrewAI function (using simplified version)
        from agents.simple_excel_crew import generate_excel_with_simple_crew
        
        print("Simple CrewAI module imported successfully")
        
        # Generate Excel using simplified CrewAI
        result = generate_excel_with_simple_crew(prompt)
        
        print(f"CrewAI result: {result}")
        
        return jsonify({
            'success': True,
            'result': result,
            'message': 'CrewAI Excel generation test completed successfully'
        })
        
    except Exception as e:
        print(f"Error in test_crew_excel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'CrewAI Excel generation test failed'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting CrewAI Test Server...")
    print("📍 Server will be available at: http://127.0.0.1:5001")
    app.run(host='127.0.0.1', port=5001, debug=True)
