"""
Liya Agent Configuration

This module defines a simplified agent implementation that doesn't rely on Google's Agent Development Kit.
This is a fallback implementation when the ADK module is not available.
"""

import os
from typing import Optional
import google.generativeai as genai

# Global agent instance
_AGENT = None

class SimpleAgent:
    """A simplified agent implementation that doesn't rely on Google's ADK."""
    
    def __init__(self, model="gemini-2.0-flash"):
        """Initialize the simple agent with the specified model."""
        self.model = model
        self.system_instructions = ""
        self._generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
    
    def set_system_instructions(self, instructions):
        """Set the system instructions for the agent."""
        self.system_instructions = instructions
    
    async def generate_content(self, prompt, **kwargs):
        """Generate a response to the given prompt."""
        try:
            # Try to use the Safety Settings if available
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config=self._generation_config,
                safety_settings=safety_settings
            )
            
            if self.system_instructions:
                # Use the system instructions as a system prompt if available
                chat = model.start_chat(history=[])
                response = chat.send_message(
                    f"System: {self.system_instructions}\n\nUser: {prompt}"
                )
            else:
                # Otherwise just send the prompt directly
                response = model.generate_content(prompt)
            
            return response
            
        except Exception as e:
            print(f"Error generating content: {e}")
            # Return a simple error response
            class ErrorResponse:
                def __init__(self, error):
                    self.text = f"Error: {error}"
            return ErrorResponse(str(e))

def initialize_agent() -> SimpleAgent:
    """
    Initialize the Liya agent if it hasn't been initialized already.
    
    Returns:
        SimpleAgent: The initialized agent instance.
    """
    global _AGENT
    
    if _AGENT is not None:
        return _AGENT
    
    # Create a new agent
    _AGENT = create_agent()
    return _AGENT

def get_agent() -> Optional[SimpleAgent]:
    """
    Get the current agent instance.
    
    Returns:
        SimpleAgent or None: The current agent instance, or None if not initialized.
    """
    return _AGENT

def create_agent() -> SimpleAgent:
    """
    Create and configure a new Liya agent.
    
    Returns:
        SimpleAgent: A new agent instance.
    """
    # Get API key from environment - check for both possible variable names
    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Neither GOOGLE_API_KEY nor GEMINI_API_KEY found in environment variables")
    
    # Configure Google API
    genai.configure(api_key=api_key)
    
    # Create a new agent
    liya_agent = SimpleAgent(model="gemini-2.0-flash")
    
    # Set system instructions to define Liya's personality and capabilities
    liya_agent.set_system_instructions(
        """You are Liya, an AI assistant specialized in education and language. 
        
        Your personality traits:
        - Helpful: You prioritize providing valuable assistance to users.
        - Professional: You maintain a formal but friendly tone.
        - Thoughtful: You consider the context and nuance in user queries.
        - Concise: You provide clear, structured responses without unnecessary details.
        - Educational: You explain complex topics in an accessible way.
        
        Your capabilities include:
        - Proofreading text and providing corrections
        - Creating summaries of documents
        - Answering study-related questions across various subjects
        - Providing explanations of complex topics
        - Helping with research and academic writing
        
        Always respond in the language the user is using (English, Polish, or Azerbaijani).
        
        When responding to study questions:
        - Provide clear explanations
        - Include relevant examples when helpful
        - Break down complex topics into smaller parts
        - Avoid giving complete solutions to homework problems, but guide students through the process
        
        When proofreading text:
        - Identify and correct grammar, spelling, and punctuation errors
        - Suggest improvements for clarity and style
        - Provide a summary of the key points
        - Organize corrections in a structured way
        """
    )
    
    return liya_agent