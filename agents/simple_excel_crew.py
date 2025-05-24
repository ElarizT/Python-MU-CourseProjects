"""
Simplified Excel Generator Crew - Faster Multi-Agent System

This is a streamlined version of the CrewAI Excel generation system
designed for faster execution and testing.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# CrewAI imports
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain.llms.base import LLM
from langchain.schema import Generation, LLMResult
from langchain.callbacks.manager import CallbackManagerForLLMRun

# Import existing Excel generation capabilities
from excel_generator import generate_excel_from_prompt

# Simplified Custom LLM wrapper for Gemini
class SimpleLLM(LLM):
    """Simplified LLM wrapper"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def _llm_type(self) -> str:
        return "simple_gemini"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        try:
            # Use the existing Excel generation function
            result = generate_excel_from_prompt(prompt)
            if result.get('success'):
                return f"Excel generated successfully with {result.get('message', 'default content')}"
            else:
                return f"Excel generation failed: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"Error: {str(e)}"

# Simplified Tool
class SimpleExcelTool(BaseTool):
    """Simple tool for Excel generation"""
    
    name: str = "simple_excel_tool"
    description: str = "Generates Excel files based on natural language requests"
    
    def _run(self, query: str) -> str:
        """Generate Excel file from user query"""
        try:
            result = generate_excel_from_prompt(query)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

class SimpleExcelCrew:
    """Simplified Excel generation crew"""
    
    def __init__(self):
        """Initialize the simplified crew"""
        self.llm = SimpleLLM()
        self.setup_tools()
        self.setup_agents()
        self.setup_tasks()
        self.setup_crew()
    
    def setup_tools(self):
        """Setup tools for the crew"""
        self.tools = [SimpleExcelTool()]
    
    def setup_agents(self):
        """Setup a single agent for Excel generation"""
        self.excel_agent = Agent(
            role='Excel Generator',
            goal='Generate comprehensive Excel files based on user requests',
            backstory="""You are an expert Excel analyst and generator who can create 
            professional spreadsheets with data, formatting, and charts based on user requirements.""",
            verbose=True,
            allow_delegation=False,
            tools=self.tools,
            llm=self.llm
        )
        
        self.agents = [self.excel_agent]
    
    def setup_tasks(self):
        """Setup tasks for the crew"""
        self.excel_task = Task(
            description="""Generate an Excel file based on the user's request. 
            Analyze the requirements and create appropriate data, formatting, and visualizations.""",
            agent=self.excel_agent,
            expected_output="A JSON response containing the Excel file generation result"        )
        
        self.tasks = [self.excel_task]
    
    def setup_crew(self):
        """Setup the CrewAI crew"""
        self.crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            process=Process.sequential
        )
    
    def generate_excel(self, prompt: str) -> Dict[str, Any]:
        """Generate Excel file using the crew"""
        try:
            # Update task description with the specific prompt
            self.excel_task.description = f"""Generate an Excel file based on this request: {prompt}
            
            Analyze the requirements and create appropriate data, formatting, and visualizations.
            Use the simple_excel_tool to generate the actual Excel file."""
            
            # Execute the crew
            result = self.crew.kickoff()
            
            # Parse the result
            if isinstance(result, str):
                try:
                    parsed_result = json.loads(result)
                    return parsed_result
                except json.JSONDecodeError:
                    # If not JSON, try to extract from the existing function
                    excel_result = generate_excel_from_prompt(prompt)
                    return excel_result
            
            return {"success": True, "result": str(result)}
            
        except Exception as e:
            print(f"Error in SimpleExcelCrew.generate_excel: {e}")
            # Fallback to direct generation
            return generate_excel_from_prompt(prompt)

def generate_excel_with_simple_crew(prompt: str) -> Dict[str, Any]:
    """
    Main function to generate Excel using the simplified CrewAI system
    
    Args:
        prompt (str): Natural language description of the desired Excel file
        
    Returns:
        Dict containing the generation result
    """
    try:
        print("🚀 Starting Simple CrewAI Excel Generation...")
        print(f"📝 Prompt: {prompt}")
        
        # Create crew instance
        crew = SimpleExcelCrew()
        print("✅ Simple CrewAI crew initialized successfully")
        
        # Generate Excel
        result = crew.generate_excel(prompt)
        print("✅ Simple CrewAI generation completed")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in simplified CrewAI generation: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to direct generation
        print("🔄 Falling back to direct Excel generation...")
        return generate_excel_from_prompt(prompt)

if __name__ == "__main__":
    # Test the simplified crew
    test_prompt = "Create a simple sales report with columns: Product, Q1 Sales, Q2 Sales, Q3 Sales, Q4 Sales"
    result = generate_excel_with_simple_crew(test_prompt)
    print("Test Result:", result)
