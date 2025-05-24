#!/usr/bin/env python3
"""
Test script for CrewAI Excel generation integration
This script tests the multi-agent CrewAI system for Excel generation
"""

import requests
import json
import time

def test_crewai_endpoint():
    """Test the CrewAI Excel generation endpoint"""
      # Test endpoint URL
    url = "http://127.0.0.1:5001/test_crew_excel"
    
    # Test prompt for Excel generation
    test_data = {
        "prompt": "Create a quarterly sales report for 2024 with the following data: Q1 sales $50,000, Q2 sales $65,000, Q3 sales $58,000, Q4 sales $72,000. Include a chart showing the quarterly trends and format it professionally."
    }
    
    print("🚀 Testing CrewAI Excel Generation Integration")
    print(f"📍 Endpoint: {url}")
    print(f"📝 Prompt: {test_data['prompt']}")
    print("\n" + "="*60)
    
    try:
        print("⏳ Sending request to CrewAI endpoint...")
        start_time = time.time()
        
        # Make the request
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=120  # 2 minute timeout for AI processing
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        # Check if request was successful
        if response.status_code == 200:
            try:
                result = response.json()
                print("\n✅ SUCCESS! CrewAI Integration Test Passed")
                print("\n📋 Response Summary:")
                print(f"   • Success: {result.get('success', 'Unknown')}")
                print(f"   • Message: {result.get('message', 'No message')}")
                
                # Check if we have crew result data
                if 'result' in result and result['result']:
                    crew_result = result['result']
                    print(f"\n🤖 Multi-Agent CrewAI Results:")
                    
                    # Display agent information
                    if 'agents_used' in crew_result:
                        print(f"   • Agents Used: {len(crew_result['agents_used'])}")
                        for agent in crew_result['agents_used']:
                            print(f"     - {agent}")
                    
                    # Display workflow information
                    if 'workflow_steps' in crew_result:
                        print(f"   • Workflow Steps: {len(crew_result['workflow_steps'])}")
                        for i, step in enumerate(crew_result['workflow_steps'][:3], 1):  # Show first 3 steps
                            print(f"     {i}. {step}")
                    
                    # Display file information
                    if 'file_path' in crew_result:
                        print(f"   • Generated File: {crew_result['file_path']}")
                    
                    # Display insights
                    if 'insights' in crew_result:
                        print(f"   • AI Insights: {crew_result['insights'][:100]}..." if len(crew_result['insights']) > 100 else f"   • AI Insights: {crew_result['insights']}")
                
                print("\n🎉 CrewAI multi-agent system is working correctly!")
                return True
                
            except json.JSONDecodeError:
                print(f"\n❌ ERROR: Invalid JSON response")
                print(f"Raw response: {response.text[:500]}...")
                return False
                
        else:
            print(f"\n❌ ERROR: Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Raw response: {response.text[:500]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to Flask server")
        print("   Make sure the Flask app is running on http://127.0.0.1:5000")
        return False
        
    except requests.exceptions.Timeout:
        print(f"\n⏰ ERROR: Request timed out after 120 seconds")
        print("   The CrewAI processing is taking longer than expected")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error occurred: {str(e)}")
        return False

def test_server_connection():
    """Test if the Flask server is running"""
    try:
        response = requests.get("http://127.0.0.1:5001/", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🔧 CrewAI Integration Test Suite")
    print("=" * 50)
    
    # First check if server is running
    if not test_server_connection():
        print("❌ Flask server is not running!")
        print("   Please start the server with: python app.py")
        exit(1)
    
    print("✅ Flask server is running")
    print("\n🧪 Starting CrewAI endpoint test...")
    
    # Run the main test
    success = test_crewai_endpoint()
    
    if success:
        print("\n🎊 All tests passed! CrewAI integration is working correctly.")
        print("   You can now use the multi-agent Excel generation in the web interface.")
    else:
        print("\n🔧 Some tests failed. Check the error messages above.")
        print("   You may need to debug the CrewAI integration.")
    
    print("\n" + "="*60)
    print("Test completed.")
