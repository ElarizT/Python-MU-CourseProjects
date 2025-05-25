"""
Interactive Agent Testing Script

This script provides a simple command-line interface to interact with
the Liya agent and test its capabilities in real-time.
"""

import os
import asyncio
import uuid
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for required API keys before importing agent modules
def check_api_keys():
    """Check if the required API keys are present in environment variables"""
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
        print("\n⚠️ ERROR: GEMINI_API_KEY not found or not set in environment variables.")
        print("Please follow these steps to set up your API key:")
        print("1. Get a Gemini API key from https://ai.google.dev/")
        print("2. Open the .env file in your project directory")
        print("3. Replace 'your_gemini_api_key_here' with your actual API key")
        print("4. Save the file and run this script again\n")
        return False
    return True

# Check API keys before proceeding
if not check_api_keys():
    sys.exit(1)

# Import agent functionality - only import after API key check
from agents.liya_agent import initialize_agent, get_agent
from agents.plans import execute_agent_with_plan

async def interactive_test():
    """Run an interactive test session with the Liya agent"""
    print("\n===== LIYA AGENT INTERACTIVE TESTING =====\n")
    print("This tool allows you to interact with the Liya agent to test its capabilities.")
    print("You can use the following commands:")
    print("  !mode study     - Switch to study assistant mode")
    print("  !mode proofread - Switch to proofreading mode")
    print("  !exit           - Exit the interactive session")
    print("\nStarting in study assistant mode...\n")
    
    try:
        # Initialize the agent
        print("Initializing Liya agent...")
        agent = initialize_agent()
        print("Agent initialized successfully!")
        
        # Set default mode
        mode = "study_assistant"
        session_id = f"interactive_{str(uuid.uuid4())[:8]}"
        
        while True:
            # Get user input
            if mode == "study_assistant":
                user_input = input("\n[Study Mode] Enter your question (or command): ")
            else:
                user_input = input("\n[Proofread Mode] Enter your text (or command): ")
            
            # Handle commands
            if user_input.lower() == "!exit":
                print("\nExiting interactive test session. Thank you!")
                break
            elif user_input.lower() == "!mode study":
                mode = "study_assistant"
                print("\nSwitched to study assistant mode")
                continue
            elif user_input.lower() == "!mode proofread":
                mode = "proofread_and_summarize"
                print("\nSwitched to proofreading mode")
                continue
            elif not user_input.strip():
                continue
            
            # Execute the appropriate plan
            try:
                print("\nProcessing your input with Liya agent...\n")
                
                result = await execute_agent_with_plan(
                    agent=agent,
                    plan_name=mode,
                    user_input=user_input,
                    user_id="interactive_user",
                    session_id=session_id
                )
                
                # Print the response
                print("\n----- LIYA'S RESPONSE -----\n")
                print(result["response"])
                print("\n---------------------------\n")
                
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Try another input or enter !exit to quit.")
                
    except Exception as e:
        print(f"\nError initializing the agent: {str(e)}")
        print("Please ensure your API key is correctly set in the .env file.")

if __name__ == "__main__":
    # Run the interactive test
    asyncio.run(interactive_test())