"""
App-Specific MCP Test Script

This script tests the integration of Model Context Protocol with your app's features.
It verifies that the MCP integration works with your study, entertainment, and proofreading features.
"""

import asyncio
import os
import json
from pprint import pprint
from dotenv import load_dotenv
import google.generativeai as genai

# Import MCP components
from mcp.context import MCPContext, ContextType
from mcp.model_adapter import MCPModelFactory

# Import app-specific utils for MCP
from agents.utils import (
    create_mcp_context_from_inputs,
    extract_metrics_from_mcp_response,
    load_user_memory_into_mcp_context
)

# Import agent execution functions
from agents.plans import (
    study_assistant_plan_with_mcp,
    proofread_and_summarize_plan_with_mcp,
    entertainment_chat_plan_with_mcp,
    execute_agent_with_mcp_plan
)

# Load environment variables (for API keys)
load_dotenv()

# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("ERROR: GOOGLE_API_KEY not found in environment variables")
    exit(1)

# Mock objects for testing
class MockAgent:
    def __init__(self):
        pass
    
    async def generate_content(self, prompt):
        # This is just a mock that returns the prompt
        return MockResponse(f"Mock response to: {prompt[:50]}...")

class MockResponse:
    def __init__(self, text):
        self.text = text

# Test functions
async def test_study_assistant():
    """Test the study assistant feature with MCP."""
    print("\n=== Testing Study Assistant with MCP ===")
    
    # Prepare inputs
    inputs = {
        "query": "Explain the concept of photosynthesis in simple terms",
        "document_text": None,
        "session_id": "test_session_1234",
        "chat_history": [
            {"role": "user", "content": "Hello, I'm studying biology"},
            {"role": "assistant", "content": "Great! Biology is fascinating. How can I help?"}
        ]
    }
    
    # Create a mock agent
    agent = MockAgent()
    
    # Execute the plan
    try:
        result = await study_assistant_plan_with_mcp(agent, inputs, user_id="test_user_1")
        print(f"Success: {result.get('success', False)}")
        print(f"Response preview: {result.get('response', '')[:100]}...")
        return "response" in result and result["success"] == True
    except Exception as e:
        print(f"Error testing study assistant: {e}")
        return False

async def test_proofread():
    """Test the proofreading feature with MCP."""
    print("\n=== Testing Proofreading with MCP ===")
    
    # Prepare inputs with intentional errors
    inputs = {
        "text": "The cat sat on the mat. It was happi to be thier. The sun was shineing brightly.",
        "session_id": "test_session_5678"
    }
    
    # Create a mock agent
    agent = MockAgent()
    
    # Execute the plan
    try:
        result = await proofread_and_summarize_plan_with_mcp(agent, inputs, user_id="test_user_2")
        print(f"Success: {result.get('success', False)}")
        print(f"Response preview: {result.get('response', '')[:100]}...")
        print(f"Sections: {list(result.get('sections', {}).keys())}")
        return "response" in result and "sections" in result
    except Exception as e:
        print(f"Error testing proofreading: {e}")
        return False

async def test_entertainment_chat():
    """Test the entertainment chat feature with MCP."""
    print("\n=== Testing Entertainment Chat with MCP ===")
    
    # Prepare inputs
    inputs = {
        "message": "Suggest some good sci-fi movies from the last 5 years",
        "category": "movies",
        "session_id": "test_session_9012",
        "chat_history": [
            {"role": "user", "content": "I love science fiction movies"},
            {"role": "assistant", "content": "Me too! Science fiction is a fascinating genre."}
        ]
    }
    
    # Create a mock agent
    agent = MockAgent()
    
    # Execute the plan
    try:
        result = await entertainment_chat_plan_with_mcp(agent, inputs, user_id="test_user_3")
        print(f"Success: {result.get('success', False)}")
        print(f"Response preview: {result.get('response', '')[:100]}...")
        return "response" in result and "category" in result
    except Exception as e:
        print(f"Error testing entertainment chat: {e}")
        return False

async def test_mcp_context_creation():
    """Test the MCP context creation utilities."""
    print("\n=== Testing MCP Context Creation Utilities ===")
    
    # Create a context with the utility function
    try:
        context = create_mcp_context_from_inputs(
            user_input="How does photosynthesis work?",
            user_id="test_user_4",
            session_id="test_session_4321",
            document_text="Photosynthesis is the process by which plants convert light energy into chemical energy.",
            chat_history=[
                {"role": "user", "content": "I'm studying plant biology"},
                {"role": "assistant", "content": "That's great! Plant biology is fascinating."}
            ],
            context_type="study"
        )
        
        # Check the context contents
        doc_elements = [e for e in context.elements if e.type == ContextType.DOCUMENT]
        chat_length = len(context.conversation_history)
        
        print(f"Context created successfully!")
        print(f"User ID: {context.user_id}")
        print(f"Session ID: {context.session_id}")
        print(f"Conversation messages: {chat_length}")
        print(f"Has document content: {len(doc_elements) > 0}")
        
        return (
            context.user_id == "test_user_4" and
            context.session_id == "test_session_4321" and
            chat_length >= 3 and  # 2 from history plus the current query
            len(doc_elements) > 0
        )
    except Exception as e:
        print(f"Error testing context creation: {e}")
        return False

async def test_agent_with_mcp_plan():
    """Test the execute_agent_with_mcp_plan function."""
    print("\n=== Testing execute_agent_with_mcp_plan ===")
    
    # Create a mock agent
    agent = MockAgent()
    
    # Try to execute a plan
    try:
        result = await execute_agent_with_mcp_plan(
            agent=agent,
            plan_name="study_assistant",
            user_input="Explain quantum physics in simple terms",
            user_id="test_user_5",
            session_id="test_session_5555",
            document_text=None,
            chat_history=None
        )
        
        print(f"Plan execution result:")
        print(f"- Plan name: {result.get('plan_name')}")
        print(f"- Response preview: {result.get('response', '')[:100]}...")
        
        return "response" in result and result.get("plan_name") == "study_assistant"
    except Exception as e:
        print(f"Error testing agent with MCP plan: {e}")
        return False

async def run_app_tests():
    """Run all app-specific MCP tests and report results."""
    print("\n🔍 STARTING APP-SPECIFIC MCP TESTS 🔍\n")
    
    tests = [
        ("MCP Context Creation", test_mcp_context_creation),
        ("Study Assistant Feature", test_study_assistant),
        ("Proofreading Feature", test_proofread),
        ("Entertainment Chat Feature", test_entertainment_chat),
        ("Agent with MCP Plan", test_agent_with_mcp_plan)
    ]
    
    results = {}
    all_passed = True
    
    for name, test_func in tests:
        try:
            print(f"\n▶️ Running test: {name}...")
            result = await test_func()
            results[name] = "✅ PASSED" if result else "❌ FAILED"
            if not result:
                all_passed = False
        except Exception as e:
            print(f"Error during test {name}: {e}")
            results[name] = f"❌ ERROR: {str(e)}"
            all_passed = False
    
    # Print summary
    print("\n\n📋 APP MCP TEST RESULTS SUMMARY 📋")
    print("=" * 50)
    for name, result in results.items():
        print(f"{name.ljust(30)}: {result}")
    print("=" * 50)
    print(f"Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    print("Running App-Specific MCP Tests...")
    asyncio.run(run_app_tests())