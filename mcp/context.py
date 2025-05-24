"""
MCP Context Module

This module provides the core components for implementing the Model Context Protocol (MCP).
It defines standardized ways to manage context information for AI model interactions.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import json
import time
from enum import Enum
import os

class ContextType(Enum):
    """Enum defining supported context types."""
    CONVERSATION = "conversation"
    DOCUMENT = "document"
    USER_MEMORY = "user_memory"
    SYSTEM_INSTRUCTION = "system_instruction"
    TOOL_RESULT = "tool_result"
    IMAGE = "image"
    PDF = "pdf"
    MULTIMODAL = "multimodal"


@dataclass
class ContextMetadata:
    """Metadata for context elements."""
    created_at: float = field(default_factory=time.time)
    source: str = "user_input"
    importance: int = 5  # 1-10 scale for priority
    ttl: Optional[int] = None  # Time-to-live in seconds, None for permanent
    mime_type: str = "text/plain"


@dataclass
class ContextElement:
    """A single piece of context."""
    content: Any
    type: ContextType
    metadata: ContextMetadata = field(default_factory=ContextMetadata)
    
    def is_expired(self) -> bool:
        """Check if this context element has expired."""
        if self.metadata.ttl is None:
            return False
        return time.time() > self.metadata.created_at + self.metadata.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "content": self.content,
            "type": self.type.value,
            "metadata": {
                "created_at": self.metadata.created_at,
                "source": self.metadata.source,
                "importance": self.metadata.importance,
                "ttl": self.metadata.ttl,
                "mime_type": self.metadata.mime_type
            }
        }


@dataclass
class ConversationMessage:
    """A message in a conversation."""
    role: str  # "user", "assistant", "system", etc.
    content: str
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(int(time.time() * 1000)))


class MCPContext:
    """Main context container for Model Context Protocol."""
    
    def __init__(self):
        self.elements: List[ContextElement] = []
        self.conversation_history: List[ConversationMessage] = []
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
    
    def add_element(self, content: Any, type_: ContextType, 
                  metadata: Optional[ContextMetadata] = None) -> None:
        """Add a context element."""
        if metadata is None:
            metadata = ContextMetadata()
        
        element = ContextElement(content, type_, metadata)
        self.elements.append(element)
    
    def add_conversation_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        message = ConversationMessage(role, content)
        self.conversation_history.append(message)
        
        # Also add as a context element
        metadata = ContextMetadata(source="conversation")
        self.add_element(
            {"role": role, "content": content},
            ContextType.CONVERSATION,
            metadata
        )
    
    def add_system_instruction(self, instruction: str) -> None:
        """Add a system instruction as context."""
        metadata = ContextMetadata(importance=10, source="system")
        self.add_element(instruction, ContextType.SYSTEM_INSTRUCTION, metadata)
    
    def add_document(self, content: str, mime_type: str = "text/plain", 
                   importance: int = 5) -> None:
        """Add a document as context."""
        metadata = ContextMetadata(
            mime_type=mime_type,
            importance=importance,
            source="document"
        )
        self.add_element(content, ContextType.DOCUMENT, metadata)
    
    def add_user_memory(self, memory_data: Dict[str, Any], 
                       importance: int = 7) -> None:
        """Add user memory data as context."""
        metadata = ContextMetadata(importance=importance, source="user_memory")
        self.add_element(memory_data, ContextType.USER_MEMORY, metadata)
    
    def add_tool_result(self, result: Any, tool_name: str, 
                      importance: int = 6) -> None:
        """Add a tool execution result as context."""
        metadata = ContextMetadata(
            importance=importance, 
            source=f"tool:{tool_name}"
        )
        self.add_element(result, ContextType.TOOL_RESULT, metadata)
    
    def add_pdf_content(self, content: str, filename: str = None) -> None:
        """Add PDF content as context."""
        metadata = ContextMetadata(
            mime_type="application/pdf",
            importance=8,
            source=filename or "pdf_document"
        )
        self.add_element(content, ContextType.PDF, metadata)
    
    def add_image(self, image_data: Union[str, bytes], 
                image_format: str = "png") -> None:
        """Add image data as context."""
        metadata = ContextMetadata(
            mime_type=f"image/{image_format}",
            importance=7,
            source="image"
        )
        self.add_element(image_data, ContextType.IMAGE, metadata)
    
    def set_user_id(self, user_id: str) -> None:
        """Set the user ID for this context."""
        self.user_id = user_id
    
    def set_session_id(self, session_id: str) -> None:
        """Set the session ID for this context."""
        self.session_id = session_id
    
    def clear_expired(self) -> None:
        """Remove expired context elements."""
        self.elements = [e for e in self.elements if not e.is_expired()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the context to dictionary format."""
        return {
            "elements": [e.to_dict() for e in self.elements],
            "conversation_history": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "message_id": m.message_id
                } for m in self.conversation_history
            ],
            "user_id": self.user_id,
            "session_id": self.session_id
        }
    
    def to_json(self) -> str:
        """Convert the context to JSON format."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPContext':
        """Create a context instance from dictionary data."""
        context = cls()
        
        # Load user and session IDs
        context.user_id = data.get("user_id")
        context.session_id = data.get("session_id")
        
        # Load conversation history
        for msg_data in data.get("conversation_history", []):
            msg = ConversationMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=msg_data.get("timestamp", time.time()),
                message_id=msg_data.get("message_id", str(int(time.time() * 1000)))
            )
            context.conversation_history.append(msg)
        
        # Load context elements
        for element_data in data.get("elements", []):
            metadata = ContextMetadata(
                created_at=element_data["metadata"].get("created_at", time.time()),
                source=element_data["metadata"].get("source", "unknown"),
                importance=element_data["metadata"].get("importance", 5),
                ttl=element_data["metadata"].get("ttl"),
                mime_type=element_data["metadata"].get("mime_type", "text/plain")
            )
            
            element = ContextElement(
                content=element_data["content"],
                type=ContextType(element_data["type"]),
                metadata=metadata
            )
            context.elements.append(element)
        
        return context
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MCPContext':
        """Create a context instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class MCPContextFactory:
    """Factory for creating specialized context objects."""
    
    @staticmethod
    def create(context_type: str = "general") -> MCPContext:
        """Create a context instance based on the specified type."""
        context = MCPContext()
        
        # Add type-specific defaults
        if context_type == "study":
            context.add_system_instruction(
                "You are a helpful study assistant. You help users understand complex topics, "
                "answer questions about their study materials, and provide educational support."
            )
        elif context_type == "entertainment":
            context.add_system_instruction(
                "You are an entertainment assistant. You can discuss movies, music, books, and other "
                "forms of entertainment. You provide recommendations and engage in casual conversation."
            )
        elif context_type == "proofread":
            context.add_system_instruction(
                "You are a proofreading assistant. You help users improve their writing by "
                "identifying grammar issues, enhancing clarity, and suggesting improvements."
            )
        
        return context