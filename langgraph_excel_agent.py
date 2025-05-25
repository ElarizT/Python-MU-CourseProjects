"""
Advanced Excel Generator Agent using LangGraph

This module creates an autonomous agent that can process Excel files,
understand natural language instructions, and perform complex data operations
using LangGraph for orchestration and Claude Sonnet 4 for reasoning.
"""

import os
import json
import uuid
import tempfile
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter
import io
import base64

# LangGraph imports
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import Annotated

# Claude API imports
import google.generativeai as genai
from dotenv import load_dotenv

# Import existing excel functionality
from excel_generator import generate_excel_from_dict_xlsx, parse_gemini_response

load_dotenv()

# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Agent State Schema
class ExcelAgentState:
    """State management for the Excel Agent workflow"""
    
    def __init__(self):
        self.messages: Annotated[list, add_messages] = []
        self.uploaded_file: Optional[Dict[str, Any]] = None
        self.file_analysis: Optional[Dict[str, Any]] = None
        self.user_intent: Optional[str] = None
        self.operation_plan: Optional[List[Dict[str, Any]]] = None
        self.current_operation: Optional[Dict[str, Any]] = None
        self.operation_result: Optional[Dict[str, Any]] = None
        self.thinking_log: List[str] = []
        self.final_output: Optional[Dict[str, Any]] = None
        self.error_state: Optional[str] = None
        self.session_id: str = str(uuid.uuid4())

class ExcelAgent:
    """
    Advanced Excel Agent using LangGraph for autonomous Excel file processing
    """
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.memory = MemorySaver()
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(dict)
        
        # Add nodes (functions)
        workflow.add_node("read_file", self.read_file_node)
        workflow.add_node("interpret_user_intent", self.interpret_user_intent_node)
        workflow.add_node("plan_tasks", self.plan_tasks_node)
        workflow.add_node("perform_operation", self.perform_operation_node)
        workflow.add_node("reflect", self.reflect_node)
        workflow.add_node("display_thinking", self.display_thinking_node)
        workflow.add_node("respond", self.respond_node)
        
        # Add edges (transitions)
        workflow.add_edge(START, "read_file")
        workflow.add_edge("read_file", "interpret_user_intent")
        
        # Conditional routing based on intent
        workflow.add_conditional_edges(
            "interpret_user_intent",
            self._route_based_on_intent,
            {
                "analysis": "perform_operation",
                "transformation": "plan_tasks",
                "error": "respond"
            }
        )
        
        workflow.add_edge("plan_tasks", "perform_operation")
        workflow.add_edge("perform_operation", "reflect")
        workflow.add_edge("reflect", "display_thinking")
        workflow.add_edge("display_thinking", "respond")
        workflow.add_edge("respond", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _route_based_on_intent(self, state: Dict[str, Any]) -> str:
        """Route workflow based on interpreted user intent"""
        intent = state.get("user_intent", "")
        
        if "error" in intent.lower():
            return "error"
        elif any(keyword in intent.lower() for keyword in ["analyze", "question", "summarize", "explain"]):
            return "analysis"
        elif any(keyword in intent.lower() for keyword in ["modify", "transform", "filter", "group", "pivot", "create"]):
            return "transformation"
        else:
            return "analysis"  # Default to analysis
    
    async def read_file_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node: Parse uploaded Excel file and extract schema and preview
        """
        thinking = "🔍 **Reading and analyzing the uploaded Excel file...**"
        state["thinking_log"] = state.get("thinking_log", []) + [thinking]
        
        try:
            file_data = state.get("uploaded_file")
            if not file_data:
                state["error_state"] = "No file uploaded"
                return state
            
            # Read the Excel file
            if file_data.get("type") == "base64":
                # Decode base64 file content
                file_content = base64.b64decode(file_data["content"])
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                # Read from file path
                df = pd.read_excel(file_data["path"])
            
            # Extract file analysis
            analysis = {
                "filename": file_data.get("filename", "uploaded_file.xlsx"),
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "preview": df.head(5).to_dict('records'),
                "missing_values": df.isnull().sum().to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "has_duplicates": df.duplicated().any()
            }
            
            state["file_analysis"] = analysis
            state["thinking_log"].append(f"✅ **File analyzed:** {analysis['shape'][0]} rows, {analysis['shape'][1]} columns")
            
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            state["error_state"] = error_msg
            state["thinking_log"].append(f"❌ **Error:** {error_msg}")
        
        return state
    
    async def interpret_user_intent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node: Use Claude to classify the user's instruction
        """
        thinking = "🧠 **Understanding your request and determining the best approach...**"
        state["thinking_log"] = state.get("thinking_log", []) + [thinking]
        
        try:
            user_instruction = state.get("user_instruction", "")
            file_analysis = state.get("file_analysis", {})
            
            # Create a detailed prompt for Claude
            analysis_prompt = f"""
<smoothly_flowing_prose_paragraphs>
You are an expert data analyst examining an Excel file and user instructions. Based on the file structure and the user's request, determine the intent and provide a classification.

**File Analysis:**
- Filename: {file_analysis.get('filename', 'N/A')}
- Dimensions: {file_analysis.get('shape', [0, 0])[0]} rows × {file_analysis.get('shape', [0, 0])[1]} columns
- Columns: {', '.join(file_analysis.get('columns', []))}
- Data types: {json.dumps(file_analysis.get('dtypes', {}), default=str)}

**User Instruction:**
"{user_instruction}"

Classify this request as either:
1. **ANALYSIS** - Questions about the data, summaries, insights, statistics
2. **TRANSFORMATION** - Modifications to the data structure, filtering, grouping, pivoting, creating new sheets

Respond with your classification and reasoning in a clear, flowing explanation.
</smoothly_flowing_prose_paragraphs>
"""
            
            response = await self._call_claude(analysis_prompt)
            
            # Extract classification from response
            if "ANALYSIS" in response.upper():
                intent = "analysis"
            elif "TRANSFORMATION" in response.upper():
                intent = "transformation"
            else:
                intent = "analysis"  # Default
            
            state["user_intent"] = intent
            state["intent_reasoning"] = response
            state["thinking_log"].append(f"🎯 **Intent classified as:** {intent.upper()}")
            
        except Exception as e:
            error_msg = f"Error interpreting intent: {str(e)}"
            state["error_state"] = error_msg
            state["thinking_log"].append(f"❌ **Error:** {error_msg}")
        
        return state
    
    async def plan_tasks_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node: Break complex tasks into steps
        """
        thinking = "📋 **Creating a step-by-step plan for your transformation...**"
        state["thinking_log"] = state.get("thinking_log", []) + [thinking]
        
        try:
            user_instruction = state.get("user_instruction", "")
            file_analysis = state.get("file_analysis", {})
            
            planning_prompt = f"""
<smoothly_flowing_prose_paragraphs>
You are an expert data transformation planner. Break down the user's request into clear, executable steps.

**File Structure:**
- {file_analysis.get('shape', [0, 0])[0]} rows × {file_analysis.get('shape', [0, 0])[1]} columns
- Columns: {', '.join(file_analysis.get('columns', []))}

**User Request:**
"{user_instruction}"

Create a detailed execution plan with the following format:
1. **Step Name** - Brief description of what this step accomplishes
2. **Operation Type** - (filter, group, pivot, calculate, create_sheet, etc.)
3. **Parameters** - Specific details needed for execution
4. **Expected Outcome** - What the result should look like

Provide your plan as a clear, logical sequence that will achieve the user's goal.
</smoothly_flowing_prose_paragraphs>
"""
            
            response = await self._call_claude(planning_prompt)
            
            # Parse the plan (simplified - could be more sophisticated)
            plan_steps = []
            lines = response.split('\n')
            current_step = {}
            
            for line in lines:
                if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                    if current_step:
                        plan_steps.append(current_step)
                    current_step = {"description": line.strip()}
                elif "Operation Type" in line:
                    current_step["operation"] = line.split('-', 1)[1].strip() if '-' in line else "general"
                elif "Parameters" in line:
                    current_step["parameters"] = line.split('-', 1)[1].strip() if '-' in line else ""
            
            if current_step:
                plan_steps.append(current_step)
            
            state["operation_plan"] = plan_steps
            state["planning_reasoning"] = response
            state["thinking_log"].append(f"📝 **Plan created with {len(plan_steps)} steps**")
            
        except Exception as e:
            error_msg = f"Error creating plan: {str(e)}"
            state["error_state"] = error_msg
            state["thinking_log"].append(f"❌ **Error:** {error_msg}")
        
        return state
    
    async def perform_operation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node: Execute the task using pandas or openpyxl
        """
        thinking = "⚡ **Executing the operations on your Excel data...**"
        state["thinking_log"] = state.get("thinking_log", []) + [thinking]
        
        try:
            user_instruction = state.get("user_instruction", "")
            file_analysis = state.get("file_analysis", {})
            intent = state.get("user_intent", "analysis")
            
            # Load the original data
            file_data = state.get("uploaded_file")
            if file_data.get("type") == "base64":
                file_content = base64.b64decode(file_data["content"])
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                df = pd.read_excel(file_data["path"])
            
            if intent == "analysis":
                result = await self._perform_analysis(df, user_instruction, file_analysis)
            else:
                result = await self._perform_transformation(df, user_instruction, file_analysis, state.get("operation_plan", []))
            
            state["operation_result"] = result
            state["thinking_log"].append(f"✅ **Operation completed successfully**")
            
        except Exception as e:
            error_msg = f"Error performing operation: {str(e)}"
            state["error_state"] = error_msg
            state["thinking_log"].append(f"❌ **Error:** {error_msg}")
        
        return state
    
    async def _perform_analysis(self, df: pd.DataFrame, instruction: str, file_analysis: Dict) -> Dict[str, Any]:
        """Perform data analysis operations"""
        
        analysis_prompt = f"""
<smoothly_flowing_prose_paragraphs>
You are a data analyst examining an Excel dataset. Provide insights based on the user's question.

**Dataset Overview:**
- {df.shape[0]} rows × {df.shape[1]} columns
- Columns: {', '.join(df.columns.tolist())}
- Sample data: {df.head(3).to_dict('records')}

**User Question:**
"{instruction}"

Provide a comprehensive analysis with:
1. **Direct Answer** - Address the specific question
2. **Key Insights** - Important patterns or findings
3. **Data Summary** - Relevant statistics
4. **Recommendations** - Actionable suggestions if applicable

Use clear, professional language that explains findings in an accessible way.
</smoothly_flowing_prose_paragraphs>
"""
        
        analysis_response = await self._call_claude(analysis_prompt)
        
        # Generate basic statistics
        numeric_columns = df.select_dtypes(include=['number']).columns
        stats = {}
        
        if len(numeric_columns) > 0:
            stats = {
                "numeric_summary": df[numeric_columns].describe().to_dict(),
                "correlations": df[numeric_columns].corr().to_dict() if len(numeric_columns) > 1 else {}
            }
        
        return {
            "type": "analysis",
            "response": analysis_response,
            "statistics": stats,
            "chart_suggestions": self._suggest_charts(df, instruction)
        }
    
    async def _perform_transformation(self, df: pd.DataFrame, instruction: str, file_analysis: Dict, plan: List[Dict]) -> Dict[str, Any]:
        """Perform data transformation operations"""
        
        # Create a transformation prompt for Claude to generate pandas code
        transformation_prompt = f"""
<smoothly_flowing_prose_paragraphs>
You are an expert Python programmer specializing in pandas data manipulation. Generate clean, efficient pandas code to fulfill the user's request.

**Dataset Information:**
- Shape: {df.shape[0]} rows × {df.shape[1]} columns
- Columns: {', '.join(df.columns.tolist())}
- Data types: {df.dtypes.to_dict()}

**User Request:**
"{instruction}"

Generate Python code that:
1. Uses the variable name 'df' for the input DataFrame
2. Creates a new variable 'result_df' for the transformed data
3. Is safe to execute (no file I/O, no imports)
4. Handles potential errors gracefully
5. Includes comments explaining each step

Provide ONLY the Python code, no explanations.
</smoothly_flowing_prose_paragraphs>
"""
        
        code_response = await self._call_claude(transformation_prompt)
        
        # Extract Python code (basic extraction)
        code_lines = []
        in_code_block = False
        
        for line in code_response.split('\n'):
            if line.strip().startswith('```python'):
                in_code_block = True
                continue
            elif line.strip().startswith('```'):
                in_code_block = False
                continue
            elif in_code_block or (not in_code_block and ('df' in line or 'result_df' in line)):
                code_lines.append(line)
        
        generated_code = '\n'.join(code_lines)
        
        # Execute the code safely
        try:
            local_vars = {'df': df.copy(), 'pd': pd}
            exec(generated_code, {"__builtins__": {}}, local_vars)
            result_df = local_vars.get('result_df', df)
            
            # Save to temporary Excel file
            temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
            result_df.to_excel(temp_file.name, index=False)
            
            return {
                "type": "transformation",
                "original_shape": df.shape,
                "result_shape": result_df.shape,
                "generated_code": generated_code,
                "output_file": temp_file.name,
                "preview": result_df.head(5).to_dict('records'),
                "success": True
            }
            
        except Exception as e:
            return {
                "type": "transformation",
                "generated_code": generated_code,
                "error": str(e),
                "success": False
            }
    
    def _suggest_charts(self, df: pd.DataFrame, instruction: str) -> List[Dict[str, str]]:
        """Suggest appropriate chart types based on data and instruction"""
        suggestions = []
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        if len(numeric_cols) > 0 and len(categorical_cols) > 0:
            suggestions.append({
                "type": "bar",
                "description": f"Bar chart showing {numeric_cols[0]} by {categorical_cols[0]}"
            })
        
        if len(numeric_cols) >= 2:
            suggestions.append({
                "type": "scatter",
                "description": f"Scatter plot of {numeric_cols[0]} vs {numeric_cols[1]}"
            })
        
        if "time" in instruction.lower() or "trend" in instruction.lower():
            suggestions.append({
                "type": "line",
                "description": "Line chart showing trends over time"
            })
        
        return suggestions
    
    async def reflect_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node: Use Claude to explain what was done and verify it matches user intent
        """
        thinking = "🤔 **Reflecting on the results and ensuring they meet your needs...**"
        state["thinking_log"] = state.get("thinking_log", []) + [thinking]
        
        try:
            user_instruction = state.get("user_instruction", "")
            operation_result = state.get("operation_result", {})
            intent = state.get("user_intent", "")
            
            reflection_prompt = f"""
<smoothly_flowing_prose_paragraphs>
You are a quality assurance expert reviewing the results of a data operation. Evaluate whether the outcome successfully addresses the user's request.

**Original User Request:**
"{user_instruction}"

**Operation Type:** {intent}

**Results Summary:**
{json.dumps(operation_result, default=str, indent=2)}

Provide a thoughtful reflection that:
1. **Evaluates Success** - Does the result address the user's request?
2. **Explains What Was Done** - Clearly describe the operations performed
3. **Identifies Limitations** - Any constraints or assumptions made
4. **Suggests Improvements** - How the result could be enhanced

Write in a conversational, helpful tone that builds user confidence in the results.
</smoothly_flowing_prose_paragraphs>
"""
            
            reflection_response = await self._call_claude(reflection_prompt)
            
            state["reflection"] = reflection_response
            state["thinking_log"].append("✅ **Quality check completed**")
            
        except Exception as e:
            error_msg = f"Error in reflection: {str(e)}"
            state["thinking_log"].append(f"❌ **Reflection error:** {error_msg}")
        
        return state
    
    async def display_thinking_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node: Output reasoning and step information to frontend
        """
        # This node prepares the thinking log for frontend display
        thinking_summary = {
            "steps": state.get("thinking_log", []),
            "current_step": len(state.get("thinking_log", [])),
            "total_steps": 6,  # Fixed workflow steps
            "timestamp": datetime.now().isoformat()
        }
        
        state["thinking_display"] = thinking_summary
        return state
    
    async def respond_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node: Return final answer or modified file
        """
        try:
            error_state = state.get("error_state")
            if error_state:
                state["final_output"] = {
                    "success": False,
                    "error": error_state,
                    "type": "error"
                }
                return state
            
            operation_result = state.get("operation_result", {})
            reflection = state.get("reflection", "")
            intent = state.get("user_intent", "")
            
            if intent == "analysis":
                state["final_output"] = {
                    "success": True,
                    "type": "analysis",
                    "response": operation_result.get("response", ""),
                    "statistics": operation_result.get("statistics", {}),
                    "chart_suggestions": operation_result.get("chart_suggestions", []),
                    "reflection": reflection
                }
            else:  # transformation
                if operation_result.get("success", False):
                    state["final_output"] = {
                        "success": True,
                        "type": "transformation",
                        "file_url": f"/download/temp/{os.path.basename(operation_result['output_file'])}",
                        "original_shape": operation_result["original_shape"],
                        "result_shape": operation_result["result_shape"],
                        "preview": operation_result["preview"],
                        "code_used": operation_result["generated_code"],
                        "reflection": reflection
                    }
                else:
                    state["final_output"] = {
                        "success": False,
                        "type": "transformation",
                        "error": operation_result.get("error", "Transformation failed"),
                        "code_attempted": operation_result.get("generated_code", "")
                    }
            
        except Exception as e:
            state["final_output"] = {
                "success": False,
                "error": f"Error generating response: {str(e)}",
                "type": "error"
            }
        
        return state
    
    async def _call_claude(self, prompt: str) -> str:
        """Call Claude (via Gemini) with the given prompt"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "max_output_tokens": 2048,
                }
            )
            return response.text
        except Exception as e:
            return f"Error calling model: {str(e)}"
    
    async def process_request(self, uploaded_file: Dict[str, Any], user_instruction: str) -> Dict[str, Any]:
        """
        Main entry point for processing Excel file with user instructions
        """
        # Initialize state
        initial_state = {
            "uploaded_file": uploaded_file,
            "user_instruction": user_instruction,
            "thinking_log": [],
            "session_id": str(uuid.uuid4())
        }
        
        # Run the workflow
        config = {"configurable": {"thread_id": initial_state["session_id"]}}
        final_state = await self.graph.ainvoke(initial_state, config)
        
        return final_state

# Global agent instance
excel_agent = None

def get_excel_agent() -> ExcelAgent:
    """Get or create the global Excel agent instance"""
    global excel_agent
    if excel_agent is None:
        excel_agent = ExcelAgent()
    return excel_agent

# Example usage functions for testing
async def example_analysis():
    """Example: Analyze sales data"""
    agent = get_excel_agent()
    
    # Simulate uploaded file
    sample_data = {
        "path": "sample_sales.xlsx",
        "filename": "sales_data.xlsx",
        "type": "file"
    }
    
    instruction = "Summarize sales performance across all regions and identify the top-performing products."
    
    result = await agent.process_request(sample_data, instruction)
    return result

async def example_transformation():
    """Example: Transform data"""
    agent = get_excel_agent()
    
    sample_data = {
        "path": "sample_data.xlsx", 
        "filename": "customer_data.xlsx",
        "type": "file"
    }
    
    instruction = "Remove rows where quantity is missing and group data by country to show total sales per country."
    
    result = await agent.process_request(sample_data, instruction)
    return result

async def example_sheet_creation():
    """Example: Create new sheet"""
    agent = get_excel_agent()
    
    sample_data = {
        "path": "revenue_data.xlsx",
        "filename": "financial_data.xlsx", 
        "type": "file"
    }
    
    instruction = "Add a new sheet that calculates year-over-year revenue growth for each product category."
    
    result = await agent.process_request(sample_data, instruction)
    return result

if __name__ == "__main__":
    # Test the agent
    import asyncio
    
    async def test_agent():
        print("🚀 Testing Excel Agent...")
        
        # Test analysis
        result = await example_analysis()
        print("Analysis Result:", json.dumps(result.get("final_output", {}), indent=2, default=str))
        
        print("\n" + "="*50 + "\n")
        
        # Test transformation
        result = await example_transformation()
        print("Transformation Result:", json.dumps(result.get("final_output", {}), indent=2, default=str))
    
    asyncio.run(test_agent())
