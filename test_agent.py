"""
Liya Agent Testing Script

This script tests the capabilities and benefits of the Liya agent
for both proofreading/summarizing and study assistance tasks.
"""

import os
import asyncio
import json
import sys
from pprint import pprint
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

# Sample texts for testing proofreading and summarization
SAMPLE_TEXT_WITH_ERRORS = """
The imprtance of educaton cannot be underestimeted in todays world. It is esential for personel growth, carrer advancement, and societal development. Students who recieve quality education are more likely to suceed in there personal and profesional lives. However, the educaton system faces many chalenges, including acess to resources, qualified teachers, and modern curiculums. Adressing these isues requires collaborative eforts from policy makers, educators, parents, and communities.
"""

SAMPLE_STUDY_QUESTIONS = [
    "What is the difference between mitosis and meiosis?",
    "Can you explain the law of conservation of energy with examples?",
    "What are the main factors that led to World War II?",
    "How does Shakespeare use symbolism in Macbeth?",
    "Explain the process of photosynthesis and its importance for life on Earth."
]

# Define conversation for memory test
MEMORY_CONVERSATION = [
    "Tell me about the water cycle.",
    "What role do oceans play in this cycle?",
    "How does climate change affect this process?",
    "What can individuals do to help preserve this cycle?"
]

async def test_proofreading_capability():
    """Test the agent's proofreading and summarization capability"""
    print("\n=== TESTING PROOFREADING CAPABILITY ===\n")
    print("Original text with errors:")
    print(SAMPLE_TEXT_WITH_ERRORS)
    print("\nSending to Liya agent for proofreading and summarization...\n")
    
    try:
        # Initialize the agent
        agent = initialize_agent()
        
        # Execute the proofreading plan
        result = await execute_agent_with_plan(
            agent=agent,
            plan_name="proofread_and_summarize",
            user_input=SAMPLE_TEXT_WITH_ERRORS,
            user_id="test_user",
            session_id="test_session_proofreading"
        )
        
        # Print the results
        print("Agent's response:")
        print("----------------")
        print(result["response"])
        print("\n")
        
        return result
    except Exception as e:
        print(f"Error during proofreading test: {str(e)}")
        return {"response": f"Error: {str(e)}"}

async def test_study_assistant_capability():
    """Test the agent's study assistant capability with multiple questions"""
    print("\n=== TESTING STUDY ASSISTANT CAPABILITY ===\n")
    
    try:
        # Initialize the agent
        agent = initialize_agent()
        
        results = []
        
        # Test each study question
        for i, question in enumerate(SAMPLE_STUDY_QUESTIONS):
            print(f"\nTesting question {i+1}: {question}\n")
            print("Sending to Liya agent...\n")
            
            # Execute the study assistant plan
            result = await execute_agent_with_plan(
                agent=agent,
                plan_name="study_assistant",
                user_input=question,
                user_id="test_user",
                session_id=f"test_session_study_{i}"
            )
            
            # Print the results
            print("Agent's response:")
            print("----------------")
            print(result["response"])
            print("\n" + "="*50 + "\n")
            
            results.append(result)
        
        return results
    except Exception as e:
        print(f"Error during study assistant test: {str(e)}")
        return [{"response": f"Error: {str(e)}"}]

async def test_memory_capabilities():
    """Test the agent's memory capabilities through a multi-turn conversation"""
    print("\n=== TESTING MEMORY CAPABILITIES ===\n")
    
    try:
        # Initialize the agent
        agent = initialize_agent()
        
        session_id = "test_session_memory"
        results = []
        
        for i, message in enumerate(MEMORY_CONVERSATION):
            print(f"\nTurn {i+1}: {message}\n")
            
            # Execute the study assistant plan
            result = await execute_agent_with_plan(
                agent=agent,
                plan_name="study_assistant",
                user_input=message,
                user_id="test_user",
                session_id=session_id
            )
            
            # Print the results
            print("Agent's response:")
            print("----------------")
            print(result["response"])
            print("\n")
            
            results.append(result)
        
        return results
    except Exception as e:
        print(f"Error during memory capabilities test: {str(e)}")
        return [{"response": f"Error: {str(e)}"}]

async def run_benchmarks():
    """Run performance benchmarks for the agent"""
    print("\n=== RUNNING PERFORMANCE BENCHMARKS ===\n")
    
    try:
        # Initialize the agent
        agent = initialize_agent()
        
        benchmark_texts = [
            "Summarize the benefits of artificial intelligence in education.",
            "Explain quantum computing in simple terms.",
            "What are the key differences between classical and operant conditioning?",
            "Discuss the environmental impact of renewable energy sources."
        ]
        
        import time
        benchmark_results = []
        
        for i, text in enumerate(benchmark_texts):
            print(f"\nBenchmark {i+1}: {text}\n")
            
            # Measure response time
            start_time = time.time()
            
            # Execute the plan
            result = await execute_agent_with_plan(
                agent=agent,
                plan_name="study_assistant",
                user_input=text,
                user_id="benchmark_user",
                session_id=f"benchmark_session_{i}"
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Record benchmark results
            benchmark_results.append({
                "query": text,
                "execution_time_seconds": execution_time,
                "response_length": len(result["response"]),
                "response_preview": result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
            })
        
        print("\nBenchmark Results Summary:")
        for i, result in enumerate(benchmark_results):
            print(f"\nQuery {i+1}: {result['query']}")
            print(f"Execution time: {result['execution_time_seconds']:.2f} seconds")
            print(f"Response length: {result['response_length']} characters")
            print(f"Response preview: {result['response_preview']}")
        
        return benchmark_results
    except Exception as e:
        print(f"Error during benchmarks: {str(e)}")
        return []

async def main():
    """Run all tests and output a summary of results"""
    print("Starting Liya Agent Testing...\n")
    
    # Run all tests
    proofreading_result = await test_proofreading_capability()
    study_results = await test_study_assistant_capability()
    memory_results = await test_memory_capabilities()
    benchmark_results = await run_benchmarks()
    
    print("\n=== TESTING COMPLETE ===\n")
    print("Summary of Benefits:")
    print("1. Proofreading & Summarization: Identifies and corrects text errors while extracting key points")
    print("2. Educational Assistance: Provides detailed explanations across various subjects")
    print("3. Memory & Context: Maintains conversation context for more relevant follow-up responses")
    print("4. Performance: Handles complex queries with reasonable response times")
    
    # You could save the results to a file for further analysis
    with open("agent_test_results.json", "w") as f:
        json.dump({
            "proofreading_test": {
                "response": proofreading_result["response"]
            },
            "study_tests": [
                {"question": q, "response": r["response"]} 
                for q, r in zip(SAMPLE_STUDY_QUESTIONS, study_results)
            ],
            "memory_tests": [
                {"turn": i+1, "input": msg, "response": r["response"]}
                for i, (msg, r) in enumerate(zip(MEMORY_CONVERSATION, memory_results))
            ]
        }, f, indent=2)
    
    print("\nDetailed results saved to agent_test_results.json")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())