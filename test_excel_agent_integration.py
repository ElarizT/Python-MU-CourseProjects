#!/usr/bin/env python3
"""
Test script for Excel Agent Integration
Tests the complete Excel agent workflow including file upload and processing
"""

import sys
import os
import requests
import json
from io import BytesIO
import pandas as pd

def create_test_excel_file():
    """Create a simple test Excel file for testing"""
    data = {
        'Name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'Age': [25, 30, 35, 28, 32],
        'Department': ['Engineering', 'Marketing', 'Sales', 'Engineering', 'HR'],
        'Salary': [75000, 65000, 55000, 80000, 60000],
        'Years_Experience': [3, 7, 5, 4, 6]
    }
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, sheet_name='Employee_Data')
    excel_buffer.seek(0)
    
    return excel_buffer

def test_excel_agent_basic():
    """Test basic Excel agent functionality without file upload"""
    base_url = "http://localhost:5000"
    
    try:
        # Test 1: Basic Excel generation (traditional endpoint)
        print("🧪 Testing basic Excel generation...")
        response = requests.post(f"{base_url}/generate_excel", 
                               json={"prompt": "Create a simple employee database with 5 employees"})
        
        if response.status_code == 200:
            print("✅ Basic Excel generation works!")
        else:
            print(f"❌ Basic Excel generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask server. Make sure it's running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error testing basic functionality: {e}")
        return False
        
    return True

def test_excel_agent_with_file():
    """Test Excel agent with file upload"""
    base_url = "http://localhost:5000"
    
    try:
        # Create test Excel file
        print("📊 Creating test Excel file...")
        excel_file = create_test_excel_file()
        
        # Test 2: Excel agent with file upload
        print("🧪 Testing Excel agent with file upload...")
        
        files = {
            'file': ('test_employees.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        data = {
            'instruction': 'Analyze this employee data and provide insights about salaries by department',
            'session_id': 'test_session_123'
        }
        
        response = requests.post(f"{base_url}/excel_agent", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Excel agent file upload works!")
            print(f"Response status: {result.get('status', 'unknown')}")
            print(f"Message: {result.get('message', 'No message')}")
            
            # Test thinking endpoint
            session_id = data['session_id']
            thinking_response = requests.get(f"{base_url}/excel_agent_thinking/{session_id}")
            
            if thinking_response.status_code == 200:
                thinking_data = thinking_response.json()
                print("✅ Thinking endpoint works!")
                print(f"Thinking log: {thinking_data.get('thinking_log', [])}")
            else:
                print(f"⚠️ Thinking endpoint returned: {thinking_response.status_code}")
                
        else:
            print(f"❌ Excel agent file upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing file upload: {e}")
        return False
        
    return True

def test_frontend_integration():
    """Test if the frontend files are properly integrated"""
    print("🎨 Testing frontend integration...")
    
    # Check if agent.js has the new Excel functionality
    try:
        with open('static/js/agent.js', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('setupExcelAgentFileUpload', 'Excel file upload setup function'),
            ('startExcelAgentThinkingPolling', 'Thinking polling function'),
            ('excel_agent', 'Excel agent endpoint usage'),
            ('excelFileUpload', 'File upload input handling')
        ]
        
        for check, description in checks:
            if check in content:
                print(f"✅ {description} found")
            else:
                print(f"❌ {description} missing")
                
    except FileNotFoundError:
        print("❌ agent.js file not found")
        return False
    except Exception as e:
        print(f"❌ Error checking frontend: {e}")
        return False
        
    # Check if CSS styles are added
    try:
        with open('static/css/unified_chat.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
            
        css_checks = [
            ('excel-agent-controls', 'Excel agent controls styling'),
            ('excel-thinking-sidebar', 'Thinking sidebar styling'),
            ('file-upload-btn', 'File upload button styling'),
            ('suggestion-chip', 'Suggestion chips styling')
        ]
        
        for check, description in css_checks:
            if check in css_content:
                print(f"✅ {description} found")
            else:
                print(f"❌ {description} missing")
                
    except FileNotFoundError:
        print("❌ unified_chat.css file not found")
        return False
    except Exception as e:
        print(f"❌ Error checking CSS: {e}")
        return False
        
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Excel Agent Integration Tests")
    print("=" * 50)
    
    # Test 1: Frontend Integration
    frontend_ok = test_frontend_integration()
    print()
    
    # Test 2: Basic Excel functionality
    basic_ok = test_excel_agent_basic()
    print()
    
    # Test 3: Excel agent with file upload
    if basic_ok:
        file_ok = test_excel_agent_with_file()
    else:
        print("⏭️ Skipping file upload test due to basic test failure")
        file_ok = False
    
    print()
    print("=" * 50)
    print("📋 Test Summary:")
    print(f"Frontend Integration: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"Basic Excel Generation: {'✅ PASS' if basic_ok else '❌ FAIL'}")
    print(f"Excel Agent File Upload: {'✅ PASS' if file_ok else '❌ FAIL'}")
    
    if frontend_ok and basic_ok and file_ok:
        print("\n🎉 All tests passed! Excel Agent is ready to use.")
        print("\n📖 Usage Instructions:")
        print("1. Start the Flask application: python app.py")
        print("2. Open your browser and go to the chat interface")
        print("3. Type '/excel' to activate the Excel agent")
        print("4. Upload an Excel file or describe what you want to create")
        print("5. Watch the thinking process in the sidebar")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
