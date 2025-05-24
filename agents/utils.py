"""
Agent Utilities

This module provides utility functions for agent memory management,
Firestore operations, and token usage tracking.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import firebase_utils as fb_utils

# Import MCP related modules
from mcp.context import MCPContext, ContextType

def track_agent_usage(user_id: str, token_count: int, plan_name: Optional[str] = None) -> None:
    """
    Track token usage for a user for billing purposes.
    
    Args:
        user_id: The user ID
        token_count: The number of tokens used
        plan_name: Optional name of the plan being used
    """
    try:
        # Get the current date for daily tracking
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Reference to the user's usage document
        usage_ref = fb_utils.db.collection('users').document(user_id) \
            .collection('usage').document(today)
        
        # Prepare update data
        update_data = {
            'tokens': fb_utils.firestore.Increment(token_count),
            'last_updated': fb_utils.firestore.SERVER_TIMESTAMP
        }
        
        # Add plan name if provided
        if plan_name:
            update_data[f'plan_{plan_name}_tokens'] = fb_utils.firestore.Increment(token_count)
        
        # Update the token count atomically
        usage_ref.set(update_data, merge=True)
    except Exception as e:
        # Log the error but don't raise it to avoid disrupting the user experience
        print(f"Error tracking token usage: {e}")

def save_to_agent_memory(
    user_id: str,
    session_id: str,
    user_input: str,
    agent_response: str
) -> bool:
    """
    Save an interaction to the agent memory for future context.
    
    Args:
        user_id: The user ID
        session_id: The session ID
        user_input: The user's input
        agent_response: The agent's response
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create a memory entry
        memory_entry = {
            'user_input': user_input,
            'agent_response': agent_response,
            'timestamp': fb_utils.firestore.SERVER_TIMESTAMP
        }
        
        # Save to memory collection
        memory_ref = fb_utils.db.collection('users').document(user_id) \
            .collection('agent_memory').document(session_id) \
            .collection('interactions').document()
        
        memory_ref.set(memory_entry)
        
        # Update the session document with metadata
        session_ref = fb_utils.db.collection('users').document(user_id) \
            .collection('agent_memory').document(session_id)
        
        session_ref.set({
            'last_interaction': fb_utils.firestore.SERVER_TIMESTAMP,
            'interaction_count': fb_utils.firestore.Increment(1)
        }, merge=True)
        
        return True
    except Exception as e:
        print(f"Error saving to agent memory: {e}")
        return False

def get_agent_memory(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Retrieve agent memory for a user, optionally filtered by session ID.
    
    Args:
        user_id: The user ID
        session_id: Optional session ID to filter by
        limit: Maximum number of memory entries to retrieve
        
    Returns:
        List of memory entries
    """
    try:
        if session_id:
            # Get memory for a specific session
            memory_ref = fb_utils.db.collection('users').document(user_id) \
                .collection('agent_memory').document(session_id) \
                .collection('interactions')
            
            query = memory_ref.order_by('timestamp', direction='DESCENDING').limit(limit)
        else:
            # Get recent memory across all sessions
            sessions_ref = fb_utils.db.collection('users').document(user_id) \
                .collection('agent_memory')
            
            # Get the most recent sessions
            recent_sessions = sessions_ref.order_by('last_interaction', direction='DESCENDING').limit(3)
            
            # Placeholder for combined results
            combined_results = []
            
            # Collect memory from each recent session
            for session_doc in recent_sessions.stream():
                session_memory = session_doc.reference.collection('interactions') \
                    .order_by('timestamp', direction='DESCENDING').limit(limit // 3)
                
                session_results = [doc.to_dict() for doc in session_memory.stream()]
                combined_results.extend(session_results)
            
            # Sort by timestamp and limit results
            combined_results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return combined_results[:limit]
        
        # Execute the query and return results
        results = [doc.to_dict() for doc in query.stream()]
        return results
    except Exception as e:
        print(f"Error retrieving agent memory: {e}")
        return []

def clear_agent_memory(user_id: str, session_id: str) -> bool:
    """
    Clear the agent memory for a specific session.
    
    Args:
        user_id: The user ID
        session_id: The session ID to clear
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get reference to the interactions collection
        interactions_ref = fb_utils.db.collection('users').document(user_id) \
            .collection('agent_memory').document(session_id) \
            .collection('interactions')
        
        # Delete all documents in the collection (batch delete)
        docs = interactions_ref.stream()
        batch = fb_utils.db.batch()
        
        for doc in docs:
            batch.delete(doc.reference)
        
        batch.commit()
        
        # Update the session document
        session_ref = fb_utils.db.collection('users').document(user_id) \
            .collection('agent_memory').document(session_id)
        
        session_ref.set({
            'interaction_count': 0,
            'cleared_at': fb_utils.firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        return True
    except Exception as e:
        print(f"Error clearing agent memory: {e}")
        return False

# New MCP-related functions

def load_user_memory_into_mcp_context(context: MCPContext, user_id: str, session_id: Optional[str] = None) -> None:
    """
    Load user memory into an MCP context.
    
    Args:
        context: The MCP context to load memory into
        user_id: The user ID
        session_id: Optional session ID to filter by
    """
    # Set the user and session IDs
    if not user_id:
        print("Warning: Attempted to load user memory with empty user_id")
        return
        
    context.set_user_id(user_id)
    if session_id:
        context.set_session_id(session_id)
    
    try:
        # Get memory entries
        memory_entries = get_agent_memory(user_id=user_id, session_id=session_id, limit=10)
        
        # Make sure we have valid entries
        if memory_entries is None:
            memory_entries = []
        
        # Add memory entries to context
        memory_data = {
            "interactions": memory_entries,
            "user_id": user_id
        }
        
        context.add_user_memory(memory_data)
    except Exception as e:
        print(f"Error loading user memory into MCP context: {e}")
        # Add minimal user memory to avoid errors
        context.add_user_memory({"interactions": [], "user_id": user_id})

def format_chat_history_for_mcp(chat_history: List[Dict[str, str]], context: MCPContext) -> None:
    """
    Format chat history and add it to an MCP context.
    
    Args:
        chat_history: List of chat messages with 'role' and 'content'
        context: The MCP context to add formatted history to
    """
    if not chat_history:
        return
    
    # Add each message to the conversation history
    for message in chat_history:
        role = message.get('role', 'user')
        content = message.get('content', '')
        if content:
            context.add_conversation_message(role, content)

def add_document_to_mcp_context(context: MCPContext, document_text: str, filename: Optional[str] = None) -> None:
    """
    Add document content to an MCP context.
    
    Args:
        context: The MCP context to add document to
        document_text: The document text content
        filename: Optional filename to determine document type
    """
    if not document_text:
        print("Warning: Empty document text provided to add_document_to_mcp_context")
        return
    
    try:
        # Ensure document text is a string
        if not isinstance(document_text, str):
            document_text = str(document_text)
        
        # Limit the document size if it's too large
        if len(document_text) > 100000:
            document_text = document_text[:100000] + "\n[Content truncated due to size limits]"
        
        # Check if we're dealing with a PDF based on filename or just assume it's a document
        if filename and filename.lower().endswith('.pdf'):
            # For PDFs, use the specialized PDF content method with higher importance
            context.add_pdf_content(document_text, filename)
        else:
            # For other document types or when filename is unknown
            context.add_document(document_text)
    except Exception as e:
        print(f"Error adding document to context: {e}")
        # Try a simplified version with lower content
        try:
            # Add just a snippet as a fallback
            snippet = document_text[:5000] + "..." if len(document_text) > 5000 else document_text
            context.add_document(snippet)
        except Exception as inner_e:
            print(f"Failed to add document snippet to context: {inner_e}")
        
    # Add an explicit element to make sure the model knows there's a document
    # and strongly indicate that responses should use this document content
    from mcp.context import ContextType, ContextMetadata
    context.add_element(
        content={
            "document_summary": f"The user has uploaded a document{f' named {filename}' if filename else ''}. The full content has been added to the context.",
            "instructions": "IMPORTANT: When responding to the user, if their question is about the document content, you MUST use the document content to answer their questions. Directly reference information from the document when answering questions about it."
        },
        type_=ContextType.USER_CONTEXT,
        metadata=ContextMetadata(source="document_reference", importance=10)
    )

def create_mcp_context_from_inputs(
    user_input: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    document_text: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    context_type: str = "general"
) -> MCPContext:
    """
    Create an MCP context from various inputs.
    
    Args:
        user_input: The current user input
        user_id: Optional user ID
        session_id: Optional session ID
        document_text: Optional document text
        chat_history: Optional chat history
        context_type: Type of context ("study", "entertainment", etc.)
        
    Returns:
        An initialized MCP context
    """
    # Create context based on type
    context = MCPContext()
    
    # Add type-specific system instruction
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
    
    # Set user and session IDs
    if user_id:
        context.set_user_id(user_id)
    if session_id:
        context.set_session_id(session_id)
      # Load user memory if user_id is provided
    if user_id:
        try:
            load_user_memory_into_mcp_context(context, user_id, session_id)
        except Exception as e:
            print(f"Warning: Failed to load user memory: {e}")
            # Continue processing without failing the whole context creation
    
    # Add chat history if provided
    if chat_history:
        try:
            format_chat_history_for_mcp(chat_history, context)
        except Exception as e:
            print(f"Warning: Failed to format chat history: {e}")
    
    # Add document content if provided
    if document_text:
        try:
            add_document_to_mcp_context(context, document_text)
        except Exception as e:
            print(f"Warning: Failed to add document to context: {e}")
    
    # Add current user input as the latest message
    context.add_conversation_message("user", user_input)
    
    return context

def extract_metrics_from_mcp_response(response) -> Dict[str, int]:
    """
    Extract usage metrics from an MCP response.
    
    Args:
        response: The MCP response object
        
    Returns:
        Dict with token usage metrics
    """
    metrics = {}
    
    if hasattr(response, 'usage_metrics'):
        metrics = response.usage_metrics
    else:
        # Rough estimate based on text length if no metrics available
        text_length = len(response.text) if hasattr(response, 'text') else 0
        metrics = {
            'prompt_tokens': 0,  # Unknown without the prompt
            'completion_tokens': text_length // 4,  # Rough estimate
            'total_tokens': text_length // 4  # Rough estimate
        }
    
    return metrics