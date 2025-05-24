"""
Model Context Protocol (MCP) Implementation

This package provides a standardized approach for AI applications to interact with context
information, creating a consistent interface for sending context to AI models and handling responses.
"""

from .context import (
    MCPContext, 
    MCPContextFactory, 
    ContextType, 
    ContextMetadata, 
    ContextElement,
    ConversationMessage
)
from .model_adapter import (
    MCPModelResponse,
    MCPModelAdapter,
    GeminiAdapter,
    MCPModelRegistry,
    MCPModelFactory
)

__all__ = [
    'MCPContext', 
    'MCPContextFactory',
    'ContextType',
    'ContextMetadata',
    'ContextElement',
    'ConversationMessage',
    'MCPModelResponse',
    'MCPModelAdapter',
    'GeminiAdapter',
    'MCPModelRegistry',
    'MCPModelFactory'
]