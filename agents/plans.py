"""
Agent Plans - Simplified Implementation

This module provides a simplified implementation of plans for the Liya agent
that doesn't rely on Google's Agent Development Kit.
"""

from typing import Dict, Any, List, Optional
import json
import asyncio

from .utils import (
    track_agent_usage, 
    save_to_agent_memory, 
    get_agent_memory, 
    create_mcp_context_from_inputs,
    extract_metrics_from_mcp_response
)

# Import MCP components
from mcp.context import MCPContext
from mcp.model_adapter import MCPModelFactory

# Simplified Plan class that mimics the functionality of google.generativeai.adk.plan.Plan
class SimplePlan:
    """A simplified plan implementation that doesn't rely on Google's ADK."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.steps = []
    
    def add_step(self, name: str, description: str, output_variable: str, 
                 tool: str = None, condition: str = None, input_mapping: Dict = None):
        """Add a step to the plan."""
        self.steps.append({
            "name": name,
            "description": description,
            "output_variable": output_variable,
            "tool": tool,
            "condition": condition,
            "input_mapping": input_mapping or {}
        })
        return self

# Plan for proofreading and summarizing text
def proofread_and_summarize_plan() -> SimplePlan:
    """
    Create a plan for proofreading and summarizing text.
    
    Returns:
        SimplePlan: A structured plan for the proofreading task.
    """
    plan = SimplePlan(
        name="proofread_and_summarize_plan",
        description="""
        Analyze, proofread, and summarize a text provided by the user.
        Identify grammar, spelling, and punctuation errors,
        provide suggestions for improving clarity and style,
        and generate a concise summary of the content.
        """,
    )
    
    # Step 1: Proofread the text
    plan.add_step(
        name="proofread_text",
        tool="proofread_text",
        description="Proofread the text to identify and correct errors.",
        output_variable="proofread_results"
    )
    
    # Step 2: Generate a summary
    plan.add_step(
        name="generate_summary",
        tool="summarize_document",
        description="Generate a concise summary of the text.",
        input_mapping={"text": "${user_input}"},
        output_variable="summary_results"
    )
    
    # Step 3: Extract key points
    plan.add_step(
        name="extract_key_points",
        tool="extract_key_points",
        description="Extract the key points from the text.",
        input_mapping={"text": "${user_input}"},
        output_variable="key_points_results"
    )
    
    # Step 4: Generate the final response
    plan.add_step(
        name="generate_response",
        description="""
        Generate a comprehensive response that includes:
        1. A list of corrections with explanations
        2. A concise summary of the text
        3. The key points from the text
        4. Suggestions for improving clarity and style
        """,
        output_variable="final_response",
    )
    
    return plan

# Plan for the study assistant functionality using MCP
async def study_assistant_plan_with_mcp(agent, inputs, user_id=None) -> dict:
    """
    Execute the study assistant functionality using MCP.
    
    Args:
        agent: The agent instance to use
        inputs: Dictionary of inputs including 'query' and optionally 'document_text'
        user_id: Optional user ID for personalization
    
    Returns:
        dict: Result containing the agent's response
    """
    # Get the inputs
    query = inputs.get('query', '')
    document_text = inputs.get('document_text', None)
    session_id = inputs.get('session_id', None)
    chat_history = inputs.get('chat_history', None)
    
    # Create MCP context
    context = create_mcp_context_from_inputs(
        user_input=query,
        user_id=user_id,
        session_id=session_id,
        document_text=document_text,
        chat_history=chat_history,
        context_type="study"
    )
    
    # Get the appropriate model adapter
    model_adapter = MCPModelFactory.create(model_name="gemini")
    
    try:
        # Generate a response using the model adapter with MCP context
        response = await model_adapter.generate_with_context(query, context)
        response_text = response.text
        
        # Extract token usage metrics
        metrics = extract_metrics_from_mcp_response(response)
        
        # Track usage if user_id is provided
        if user_id:
            track_agent_usage(user_id, metrics.get('total_tokens', 0), "study_assistant")
            
            # Save to agent memory for future context
            if session_id:
                save_to_agent_memory(
                    user_id=user_id,
                    session_id=session_id,
                    user_input=query,
                    agent_response=response_text
                )
    except Exception as e:
        print(f"Error generating study response with MCP: {e}")
        response_text = f"I'm sorry, I encountered an error while processing your question: {str(e)}"
    
    return {
        "success": True,
        "response": response_text,
        "task_type": "study_assistant"
    }

# Legacy study assistant plan function for backward compatibility
async def study_assistant_plan(agent, inputs, user_id=None) -> dict:
    """
    Execute the study assistant functionality using a simplified approach.
    
    This is maintained for backward compatibility.
    For new code, prefer study_assistant_plan_with_mcp.
    """
    # Get the inputs
    query = inputs.get('query', '')
    document_text = inputs.get('document_text', None)
    
    # Create a system prompt that encourages educational responses
    system_prompt = """
    You are a study assistant AI specialized in education and learning.
    Your goal is to provide clear, educational responses that help the user understand concepts.
    When explaining difficult topics:
    - Break them down into simpler components
    - Use examples and analogies where appropriate
    - Connect new information to concepts the user likely already understands
    - Encourage critical thinking rather than giving direct answers to homework questions
    """
    
    # Build the prompt
    if document_text:
        prompt = f"""
        The user has provided the following document:
        
        {document_text}
        
        Now they're asking: {query}
        
        Please help them understand this document by answering their question.
        """
    else:
        prompt = query
    
    # Generate a response
    try:
        # Properly await the async response
        response = await agent.generate_content(prompt)
        
        # Extract text from response
        if hasattr(response, "text"):
            response_text = response.text
        elif hasattr(response, "parts"):
            response_text = " ".join([part.text for part in response.parts])
        else:
            response_text = str(response)
    except Exception as e:
        print(f"Error generating study response: {e}")
        response_text = f"I'm sorry, I encountered an error while processing your question: {str(e)}"
    
    # Track usage if user_id is provided
    if user_id:
        # Rough estimate of token usage
        estimated_tokens = (len(query) + len(response_text)) // 4
        track_agent_usage(user_id, estimated_tokens, "study_assistant")
    
    return {
        "success": True,
        "response": response_text,
        "task_type": "study_assistant"
    }

# Proofreading plan with MCP
async def proofread_and_summarize_plan_with_mcp(agent, inputs, user_id=None) -> dict:
    """
    Execute the proofreading and summarizing functionality using MCP.
    
    Args:
        agent: The agent instance to use
        inputs: Dictionary of inputs including 'text' to proofread
        user_id: Optional user ID for personalization
    
    Returns:
        dict: Result containing the proofread text, summary, and key points
    """
    # Get the inputs
    text = inputs.get('text', '')
    session_id = inputs.get('session_id', None)
    
    # Create MCP context
    context = create_mcp_context_from_inputs(
        user_input=text,
        user_id=user_id,
        session_id=session_id,
        context_type="proofread"
    )
    
    # Add specific system instruction for proofreading
    context.add_system_instruction(
        """
        Analyze, proofread, and summarize the following text:
        1. Identify grammar, spelling, and punctuation errors
        2. Provide corrections with explanations
        3. Generate a concise summary (1-2 paragraphs)
        4. Extract 3-5 key points
        5. Suggest improvements for clarity and style
        
        Format your response as:
        
        ## Corrections
        [List corrections here with explanations]
        
        ## Summary
        [Concise summary of the text]
        
        ## Key Points
        - [Point 1]
        - [Point 2]
        - [Point 3]
        
        ## Style Suggestions
        [Provide suggestions for improving clarity and style]
        """
    )
    
    # Get the appropriate model adapter
    model_adapter = MCPModelFactory.create(model_name="gemini")
    
    try:
        # Generate a response using the model adapter with MCP context
        response = await model_adapter.generate_with_context("Please proofread this text", context)
        response_text = response.text
        
        # Extract token usage metrics
        metrics = extract_metrics_from_mcp_response(response)
        
        # Track usage if user_id is provided
        if user_id:
            track_agent_usage(user_id, metrics.get('total_tokens', 0), "proofread")
    except Exception as e:
        print(f"Error generating proofread response with MCP: {e}")
        response_text = f"I'm sorry, I encountered an error while proofreading your text: {str(e)}"
    
    # Parse the response to extract different sections
    sections = {}
    current_section = None
    
    for line in response_text.split('\n'):
        if line.startswith('##'):
            current_section = line.strip('# ').lower()
            sections[current_section] = []
        elif current_section and line.strip():
            sections[current_section].append(line)
    
    # Format results
    for section, lines in sections.items():
        sections[section] = '\n'.join(lines)
    
    return {
        "success": True,
        "response": response_text,
        "sections": sections,
        "task_type": "proofread"
    }

# Entertainment chat plan with MCP
async def entertainment_chat_plan_with_mcp(agent, inputs, user_id=None) -> dict:
    """
    Execute the entertainment chat functionality using MCP.
    
    Args:
        agent: The agent instance to use
        inputs: Dictionary of inputs including 'message' and 'category'
        user_id: Optional user ID for personalization
    
    Returns:
        dict: Result containing the agent's response
    """
    # Get the inputs
    message = inputs.get('message', '')
    category = inputs.get('category', 'general')
    session_id = inputs.get('session_id', None)
    chat_history = inputs.get('chat_history', None)
    
    # Create MCP context
    context = create_mcp_context_from_inputs(
        user_input=message,
        user_id=user_id,
        session_id=session_id,
        chat_history=chat_history,
        context_type="entertainment"
    )
    
    # Add category as context
    context.add_element(
        content={"category": category},
        type_=context.ContextType.TOOL_RESULT,
        metadata=context.ContextMetadata(source="category_selection")
    )
    
    # Get the appropriate model adapter
    model_adapter = MCPModelFactory.create(model_name="gemini")
    
    try:
        # Generate a response using the model adapter with MCP context
        response = await model_adapter.generate_with_context(message, context)
        response_text = response.text
        
        # Extract token usage metrics
        metrics = extract_metrics_from_mcp_response(response)
        
        # Track usage if user_id is provided
        if user_id:
            track_agent_usage(user_id, metrics.get('total_tokens', 0), "entertainment")
            
            # Save to agent memory for future context
            if session_id:
                save_to_agent_memory(
                    user_id=user_id,
                    session_id=session_id,
                    user_input=message,
                    agent_response=response_text
                )
    except Exception as e:
        print(f"Error generating entertainment response with MCP: {e}")
        response_text = f"I'm sorry, I encountered an error while processing your message: {str(e)}"
    
    return {
        "success": True,
        "response": response_text,
        "category": category,
        "task_type": "entertainment"
    }

# Simplified function to execute a plan with an agent using MCP
async def execute_agent_with_mcp_plan(
    agent,
    plan_name: str,
    user_input: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    document_text: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute a specific plan with the agent using MCP.
    
    Args:
        agent: The agent instance
        plan_name: The name of the plan to execute
        user_input: The user's input text
        user_id: The user's ID (optional)
        session_id: The session ID (optional)
        document_text: Document text if available (optional)
        chat_history: Chat history if available (optional)
        **kwargs: Additional keyword arguments for the plan
        
    Returns:
        Dictionary containing the agent's response and any additional data.
    """
    # Prepare inputs for the plan
    inputs = {
        "query": user_input,
        "message": user_input,
        "text": user_input,
        "document_text": document_text,
        "session_id": session_id,
        "chat_history": chat_history,
        **kwargs
    }
    
    # Select and execute the appropriate plan
    if plan_name == "study_assistant":
        result = await study_assistant_plan_with_mcp(agent, inputs, user_id)
    elif plan_name == "proofread_and_summarize":
        result = await proofread_and_summarize_plan_with_mcp(agent, inputs, user_id)
    elif plan_name == "entertainment_chat":
        result = await entertainment_chat_plan_with_mcp(agent, inputs, user_id)
    else:
        # Fall back to the legacy method for unknown plans
        return await execute_agent_with_plan(
            agent, plan_name, user_input, user_id, 
            session_id, document_text, chat_history
        )
    
    # Add common fields to the result
    result["plan_name"] = plan_name
    
    return result

# Legacy execute_agent_with_plan function for backward compatibility
async def execute_agent_with_plan(
    agent,
    plan_name: str,
    user_input: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    document_text: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Legacy function to execute a specific plan with the simplified agent.
    
    This is maintained for backward compatibility.
    For new code, prefer execute_agent_with_mcp_plan.
    """
    # In this simplified version, we'll directly use the agent to generate a response
    # without actually executing the plan steps (which would require the ADK)
    
    # Get the appropriate plan (just for context in the prompt)
    if plan_name == "proofread_and_summarize":
        plan = proofread_and_summarize_plan()
        plan_description = "Proofread and summarize the text, identifying errors and key points"
    elif plan_name == "study_assistant":
        plan = study_assistant_plan()
        plan_description = "Answer study-related questions with clear explanations and examples"
    else:
        raise ValueError(f"Unknown plan: {plan_name}")
    
    # Retrieve conversation history from memory if user_id and session_id are provided
    conversation_history = []
    if user_id and session_id:
        memory_entries = get_agent_memory(user_id=user_id, session_id=session_id, limit=10)
        
        # Format memory entries into a conversation history
        for entry in memory_entries:
            conversation_history.append({
                "role": "user",
                "content": entry.get("user_input", "")
            })
            conversation_history.append({
                "role": "assistant",
                "content": entry.get("agent_response", "")
            })
    
    # If chat_history was provided, merge it with memory entries
    if chat_history:
        # Only add items not already in conversation_history
        for item in chat_history:
            if item not in conversation_history:
                conversation_history.append(item)
    
    # Build a prompt that describes what the agent should do
    prompt = f"""
    Task: {plan_name}
    
    Description: {plan_description}
    
    User input: {user_input}
    
    {f"Document text: {document_text}" if document_text else ""}
    """
    
    # Add conversation history to the prompt if available
    if conversation_history:
        prompt += "\n\nPrevious conversation:\n"
        for message in conversation_history:
            role = message.get("role", "")
            content = message.get("content", "")
            prompt += f"{role}: {content}\n"
    
    prompt += "\nPlease provide a comprehensive response based on the task description and conversation context."
    
    # Generate a response using the agent
    response = await agent.generate_content(prompt)
    
    # Extract the response text
    if hasattr(response, "text"):
        response_text = response.text
    elif hasattr(response, "parts"):
        response_text = " ".join([part.text for part in response.parts])
    else:
        response_text = str(response)
    
    # Track token usage for billing
    if user_id:
        token_count = len(response_text.split()) // 3  # rough estimate
        track_agent_usage(user_id, token_count)
        
        # Save to agent memory for future context
        if session_id:
            save_to_agent_memory(
                user_id=user_id,
                session_id=session_id,
                user_input=user_input,
                agent_response=response_text
            )
    
    return {
        "response": response_text,
        "plan_name": plan_name,
        "additional_data": {
            "plan_description": plan_description
        }
    }