#!/usr/bin/env python3
"""
Quick test script for Excel generation
"""

print("🧪 Starting Excel generation tests...")

# Test 1: Basic Excel generation
print("\n1. Testing basic Excel generation...")
try:
    from excel_generator import generate_excel_from_prompt
    result = generate_excel_from_prompt('Create a simple table with Name, Age, City columns')
    print(f"   ✅ Basic Excel result: {result.get('success', False)}")
    if result.get('success'):
        print(f"   📊 Excel content available: {'excel_content' in result}")
        if 'excel_content' in result:
            print(f"   📏 Excel content size: {len(result['excel_content'])} bytes")
except Exception as e:
    print(f"   ❌ Basic Excel generation failed: {e}")

# Test 2: Simplified CrewAI
print("\n2. Testing simplified CrewAI...")
try:
    from agents.simple_excel_crew import generate_excel_with_simple_crew
    result = generate_excel_with_simple_crew('Create a simple table with Name, Age, City columns')
    print(f"   ✅ Simple CrewAI result: {result.get('success', False)}")
    if result.get('success'):
        print(f"   📊 Excel content available: {'excel_content' in result}")
        if 'excel_content' in result:
            print(f"   📏 Excel content size: {len(result['excel_content'])} bytes")
except Exception as e:
    print(f"   ❌ Simple CrewAI failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: HTTP endpoint test
print("\n3. Testing HTTP endpoint...")
try:
    import requests
    import json
    
    data = {'prompt': 'Create a simple Excel file with columns: Name, Age, City'}
    response = requests.post('http://127.0.0.1:5001/test_crew_excel', 
                           json=data, 
                           timeout=15)
    print(f"   📡 HTTP Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ HTTP Response keys: {list(result.keys())}")
        print(f"   📊 Success: {result.get('success', False)}")
    else:
        print(f"   ❌ HTTP Error: {response.text}")
except requests.exceptions.Timeout:
    print("   ⏰ HTTP request timed out after 15 seconds")
except Exception as e:
    print(f"   ❌ HTTP test failed: {e}")

print("\n🏁 Tests completed!")
