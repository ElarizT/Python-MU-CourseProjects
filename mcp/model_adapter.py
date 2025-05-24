"""
MCP Model Adapter Module

This module provides adapters for different AI models to work with the Model Context Protocol (MCP).
It enables a consistent interface for interacting with various models while using MCP contexts.
"""

from typing import Dict, List, Any, Optional, Union, Callable
import json
import os
import asyncio
from abc import ABC, abstractmethod

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .context import MCPContext, ContextType


class MCPModelResponse:
    """Standardized response object from model calls."""
    
    def __init__(self, 
                 text: str, 
                 raw_response: Any = None,
                 usage_metrics: Dict[str, int] = None):
        self.text = text
        self.raw_response = raw_response
        self.usage_metrics = usage_metrics or {}
    
    @property
    def content(self) -> str:
        """Alias for text."""
        return self.text


class MCPModelAdapter(ABC):
    """Base adapter class for model providers."""
    
    @abstractmethod
    async def generate_with_context(self, 
                                   prompt: str, 
                                   context: MCPContext) -> MCPModelResponse:
        """Generate a response using the given prompt and context."""
        pass
    
    @abstractmethod
    def format_context_for_model(self, context: MCPContext) -> Any:
        """Format the context in a way the specific model can understand."""
        pass


class GeminiAdapter(MCPModelAdapter):
    """Adapter for Google's Gemini models."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        """
        Initialize the Gemini adapter with the appropriate model.
        
        Note: As of May 2025, the recommended model is gemini-2.0-flash for
        fast, efficient responses with good performance and lower latency.
        """
        if genai is None:
            raise ImportError("Google GenerativeAI package is not installed. "
                             "Install with: pip install google-generativeai")
        
        # Ensure API key is set
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable must be set")
        
        # Configure the genai library with the API key
        genai.configure(api_key=api_key)
        
        # The preferred models in order of preference
        # Note that Google's API sometimes returns model names with a "models/" prefix
        preferred_models = [
            "gemini-2.0-flash",
            "models/gemini-2.0-flash",
            "models/gemini-2.0-flash-001", 
            "gemini-1.5-flash",
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-flash-001"
        ]
        
        # Try to get available models
        self.available_models = []
        try:
            self.available_models = [model.name for model in genai.list_models()]
            print(f"Available Gemini models: {self.available_models}")
        except Exception as e:
            print(f"Warning: Could not retrieve available models: {e}")
        
        # Check if the requested model is available (with or without "models/" prefix)
        self.model_name = model_name
        requested_with_prefix = f"models/{model_name}"
        
        if self.available_models:
            # If the model name doesn't exist as specified, check if it exists with the "models/" prefix
            if model_name not in self.available_models and requested_with_prefix not in self.available_models:
                # Find the first available model from our preferred list
                found_model = False
                for preferred in preferred_models:
                    if preferred in self.available_models:
                        self.model_name = preferred
                        print(f"Model '{model_name}' not found, using '{self.model_name}' instead")
                        found_model = True
                        break
                
                # If none of our preferred models are available, look for any viable Gemini model
                if not found_model:
                    # Check for good Gemini 2.0 or 1.5 models first
                    viable_models = [
                        m for m in self.available_models 
                        if "gemini-2.0-flash" in m or "gemini-1.5-flash" in m or "gemini-2.0-pro" in m
                    ]
                    
                    # If no viable models found, try any Gemini model
                    if not viable_models:
                        viable_models = [m for m in self.available_models if "gemini" in m]
                    
                    # Use the first available model from our filtered list
                    if viable_models:
                        self.model_name = viable_models[0]
                        print(f"Model '{model_name}' not found, using '{self.model_name}' instead")
        
        try:
            print(f"Initializing Gemini model: {self.model_name}")
            self.model = genai.GenerativeModel(self.model_name)
            print(f"Successfully initialized Gemini model: {self.model_name}")
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            
            # Try alternative models if initialization fails
            fallback_attempted = False
            for fallback in [m for m in self.available_models if "gemini" in m and "flash" in m]:
                if fallback != self.model_name:
                    try:
                        print(f"Attempting fallback to {fallback}")
                        self.model_name = fallback
                        self.model = genai.GenerativeModel(self.model_name)
                        print(f"Successfully initialized fallback model: {self.model_name}")
                        fallback_attempted = True
                        break
                    except Exception as fallback_error:
                        print(f"Fallback to {fallback} failed: {fallback_error}")
            
            # If all fallbacks failed, raise the original error
            if not fallback_attempted:
                raise ValueError(f"Could not initialize any available Gemini model: {e}")
    
    def format_context_for_model(self, context: MCPContext) -> List[Dict[str, Any]]:
        """Format the context for Gemini."""
        formatted_messages = []
        
        # Add system instructions
        system_instructions = [
            e.content for e in context.elements 
            if e.type == ContextType.SYSTEM_INSTRUCTION
        ]
        
        if system_instructions:
            formatted_messages.append({
                "role": "user",
                "parts": [{"text": "System Instructions:\n" + "\n".join(system_instructions)}]
            })
            # Add model response to acknowledge system instructions
            formatted_messages.append({
                "role": "model",
                "parts": [{"text": "I'll follow these instructions."}]
            })
        
        # Add conversation history
        for message in context.conversation_history:
            formatted_messages.append({
                "role": "user" if message.role == "user" else "model",
                "parts": [{"text": message.content}]
            })
        
        # Add document content if available
        documents = [
            e.content for e in context.elements 
            if e.type == ContextType.DOCUMENT
        ]
        
        if documents and formatted_messages:
            document_text = "Document content:\n"
            if len(documents) == 1:
                document_text += documents[0]
            else:
                document_text += "\n\n" + "\n\n".join(documents)
                
            # Add document content as a separate message or append to the last message
            if formatted_messages and formatted_messages[-1]["role"] == "user":
                # Append to last user message
                formatted_messages[-1]["parts"][0]["text"] += "\n\n" + document_text
            else:
                # Add as a new message
                formatted_messages.append({
                    "role": "user",
                    "parts": [{"text": document_text}]
                })
        
        # Add user memory if available
        memory_data = [
            e.content for e in context.elements 
            if e.type == ContextType.USER_MEMORY
        ]
        
        if memory_data and formatted_messages:
            memory_text = "User memory:\n" + json.dumps(memory_data[0]) if memory_data else ""
            if memory_text:
                if formatted_messages and formatted_messages[-1]["role"] == "user":
                    # Append to last user message
                    formatted_messages[-1]["parts"][0]["text"] += "\n\n" + memory_text
                else:
                    # Add as a new message
                    formatted_messages.append({
                        "role": "user",
                        "parts": [{"text": memory_text}]
                    })
        
        return formatted_messages
    
    async def generate_with_context(self, 
                                  prompt: str, 
                                  context: MCPContext) -> MCPModelResponse:
        """Generate a response using Gemini with the given context."""
        # Format conversation history
        messages = self.format_context_for_model(context)
        
        # Add the current prompt as a user message
        if not messages or messages[-1]["role"] != "user":
            messages.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })
        else:
            # Append to the last user message if it exists
            messages[-1]["parts"][0]["text"] += "\n\n" + prompt
        
        try:
            # Call the model with the formatted messages
            response = await self.model.generate_content_async(messages)
            
            # Extract text from response
            if hasattr(response, "text"):
                text = response.text
            elif hasattr(response, "parts"):
                text = " ".join([part.text for part in response.parts])
            else:
                text = str(response)
            
            # Estimate tokens (actual usage depends on model implementation)
            total_chars = sum(len(m["parts"][0]["text"]) for m in messages) + len(text)
            estimated_tokens = total_chars // 4
            
            usage_metrics = {
                "prompt_tokens": (total_chars - len(text)) // 4,
                "completion_tokens": len(text) // 4,
                "total_tokens": estimated_tokens
            }
            
            return MCPModelResponse(text=text, raw_response=response, usage_metrics=usage_metrics)
        
        except Exception as e:
            print(f"Error generating content with Gemini: {e}")
            
            # Try to provide helpful error information
            error_message = str(e)
            friendly_error = "I apologize, but I encountered an error processing your request."
            
            # Handle specific error cases
            if "404" in error_message and "not found" in error_message:
                friendly_error += " The AI model currently in use is not available. This might be due to API changes."
                if self.available_models:
                    friendly_error += f" Available models: {', '.join(self.available_models[:5])}"
            elif "quota" in error_message.lower() or "rate limit" in error_message.lower():
                friendly_error += " We've reached our API quota limit. Please try again later."
            
            # Return a graceful error response
            return MCPModelResponse(
                text=friendly_error,
                raw_response=None,
                usage_metrics={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            )


class MCPModelRegistry:
    """Registry of available model adapters."""
    
    _adapters = {}
    
    @classmethod
    def register(cls, name: str, adapter_class: type) -> None:
        """Register a model adapter."""
        cls._adapters[name] = adapter_class
    
    @classmethod
    def get(cls, name: str, **kwargs) -> MCPModelAdapter:
        """Get a model adapter by name."""
        if name not in cls._adapters:
            raise ValueError(f"Model '{name}' not registered")
        
        return cls._adapters[name](**kwargs)
    
    @classmethod
    def list_available(cls) -> List[str]:
        """List available model adapters."""
        return list(cls._adapters.keys())


# Register available adapters
MCPModelRegistry.register("gemini", GeminiAdapter)


class MCPModelFactory:
    """Factory for creating model adapters."""
    
    @staticmethod
    def create(model_name: str = "gemini", **kwargs) -> MCPModelAdapter:
        """Create a model adapter based on the model name."""
        return MCPModelRegistry.get(model_name, **kwargs)