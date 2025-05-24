"""
MCP Test Script

This script tests the Model Context Protocol implementation in your app.
It verifies the core functionality of context management and model interaction.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Import MCP components
from mcp.context import MCPContext, ContextType
from mcp.model_adapter import MCPModelFactory

# Load environment variables (for API keys)
load_dotenv()

# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("ERROR: GOOGLE_API_KEY not found in environment variables")
    exit(1)

async def test_basic_context():
    """Test basic context creation and model interaction."""
    print("\n=== Testing Basic Context ===")
    
    # Create a basic context
    context = MCPContext()
    context.add_system_instruction("You are a helpful assistant specialized in Python programming.")
    context.add_conversation_message("user", "What are the key features of Python?")
    
    # Create a model adapter
    model = MCPModelFactory.create(model_name="gemini")
    
    # Generate a response
    response = await model.generate_with_context(
        "List three key features of Python programming language",
        context
    )
    
    print(f"Response: {response.text}")
    print(f"Token metrics: {response.usage_metrics}")
    
    return response.text is not None and len(response.text) > 0

async def test_document_context():
    """Test context with document content."""
    print("\n=== Testing Document Context ===")
    
    # Create a context with document
    context = MCPContext()
    context.add_system_instruction("You are a study assistant that helps understand documents.")
    
    # Add a sample document
    sample_doc = """
    # Python Programming Language
    
    Python is a high-level, interpreted programming language known for its readability
    and ease of use. It supports multiple programming paradigms including procedural,
    object-oriented, and functional programming.
    
    ## Key Features
    
    * Simple, easy-to-learn syntax
    * Dynamically typed
    * Interpreted language
    * Extensive standard library
    * Large and active community
    """
    
    context.add_document(sample_doc)
    
    # Add conversation messages
    context.add_conversation_message("user", "What are the key features mentioned in the document?")
    
    # Create a model adapter
    model = MCPModelFactory.create(model_name="gemini")
    
    # Generate a response
    response = await model.generate_with_context(
        "Summarize the key features mentioned in the document",
        context
    )
    
    print(f"Response: {response.text}")
    print(f"Token metrics: {response.usage_metrics}")
    
    return "features" in response.text.lower() and "python" in response.text.lower()

async def test_conversation_history():
    """Test context with conversation history."""
    print("\n=== Testing Conversation History ===")
    
    # Create a context with conversation history
    context = MCPContext()
    context.add_system_instruction("You are a helpful assistant.")
    
    # Add multiple conversation turns
    context.add_conversation_message("user", "Hello, my name is Alex")
    context.add_conversation_message("assistant", "Hello Alex, how can I help you today?")
    context.add_conversation_message("user", "What's my name?")
    
    # Create a model adapter
    model = MCPModelFactory.create(model_name="gemini")
    
    # Generate a response
    response = await model.generate_with_context(
        "Please tell me what my name is based on our conversation",
        context
    )
    
    print(f"Response: {response.text}")
    print(f"Token metrics: {response.usage_metrics}")
    
    return "alex" in response.text.lower()

async def test_serialization():
    """Test serialization and deserialization of context."""
    print("\n=== Testing Serialization ===")
    
    # Create a context
    original_context = MCPContext()
    original_context.add_system_instruction("You are a helpful assistant.")
    original_context.add_conversation_message("user", "Hello!")
    original_context.set_user_id("test_user_123")
    
    # Serialize to JSON
    context_json = original_context.to_json()
    print(f"Serialized context: {context_json[:100]}...")
    
    # Deserialize from JSON
    restored_context = MCPContext.from_json(context_json)
    
    # Verify deserialization
    success = (
        restored_context.user_id == "test_user_123" and
        len(restored_context.conversation_history) == 1 and
        len(restored_context.elements) > 0
    )
    
    print(f"Deserialization success: {success}")
    return success

async def run_all_tests():
    """Run all MCP tests and report results."""
    print("\n🔍 STARTING MCP IMPLEMENTATION TESTS 🔍\n")
    
    tests = [
        ("Basic Context", test_basic_context),
        ("Document Context", test_document_context),
        ("Conversation History", test_conversation_history),
        ("Serialization", test_serialization)
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
    print("\n\n📋 TEST RESULTS SUMMARY 📋")
    print("=" * 40)
    for name, result in results.items():
        print(f"{name.ljust(25)}: {result}")
    print("=" * 40)
    print(f"Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    print("Running MCP Tests...")
    asyncio.run(run_all_tests())