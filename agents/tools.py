"""
ADK Tools Implementation

This module defines the tools that the Liya agent can use to perform
specific tasks like proofreading, summarizing, and studying.
"""

from typing import Dict, List, Any, Optional
import json
from google.generativeai.adk.tool import Function
import firebase_utils as fb_utils

# Import existing utility functions that we'll wrap as tools
try:
    from proofreading import process_text_for_proofreading, generate_corrections, create_correction_pdf
except ImportError:
    # Fallback implementations if the modules aren't available
    def process_text_for_proofreading(text):
        return {"text": text, "language": "en"}
    
    def generate_corrections(text_info):
        return {"corrections": [], "corrected_text": text_info["text"]}
    
    def create_correction_pdf(text_info, corrections):
        return {"pdf_url": None}

# Tool definitions
def proofread_text() -> Function:
    """
    Create a tool for proofreading text and identifying errors.
    
    Returns:
        Function: An ADK tool function for proofreading.
    """
    def _execute(text: str) -> Dict[str, Any]:
        """
        Execute the proofreading function on the provided text.
        
        Args:
            text: The text to proofread
            
        Returns:
            Dictionary with corrections and the corrected text.
        """
        # Process the text first to identify language and extract content
        text_info = process_text_for_proofreading(text)
        
        # Generate corrections
        correction_results = generate_corrections(text_info)
        
        # Format the results for the agent
        result = {
            "original_text": text[:1000] + "..." if len(text) > 1000 else text,
            "corrections": correction_results.get("corrections", []),
            "corrected_text": correction_results.get("corrected_text", text)
        }
        
        return result
    
    return Function(
        name="proofread_text",
        description="Proofread the given text to identify and correct grammar, spelling, and punctuation errors.",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to proofread."
                }
            },
            "required": ["text"]
        },
        function=_execute
    )

def summarize_document() -> Function:
    """
    Create a tool for summarizing a document or text.
    
    Returns:
        Function: An ADK tool function for summarization.
    """
    def _execute(text: str, max_length: Optional[int] = 500) -> Dict[str, str]:
        """
        Summarize the given text.
        
        Args:
            text: The text to summarize
            max_length: Maximum length of the summary in words
            
        Returns:
            Dictionary containing the summary.
        """
        # In a real implementation, this would use a model or service to generate a summary
        # For now, we'll return a placeholder that the agent will replace with generated content
        return {
            "summary": "[SUMMARY_PLACEHOLDER]",
            "original_length": len(text.split()),
            "summary_length": max_length
        }
    
    return Function(
        name="summarize_document",
        description="Generate a concise summary of the provided document or text.",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to summarize."
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum length of the summary in words.",
                    "default": 500
                }
            },
            "required": ["text"]
        },
        function=_execute
    )

def extract_key_points() -> Function:
    """
    Create a tool for extracting key points from text.
    
    Returns:
        Function: An ADK tool function for key point extraction.
    """
    def _execute(text: str, max_points: Optional[int] = 5) -> Dict[str, List[str]]:
        """
        Extract key points from the given text.
        
        Args:
            text: The text to analyze
            max_points: Maximum number of key points to extract
            
        Returns:
            Dictionary containing the list of key points.
        """
        # In a real implementation, this would use a model or service to extract key points
        # For now, we'll return a placeholder that the agent will replace with generated content
        return {
            "key_points": ["[KEY_POINT_PLACEHOLDER]"] * min(max_points, 5)
        }
    
    return Function(
        name="extract_key_points",
        description="Extract the main points or arguments from the provided text.",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to analyze."
                },
                "max_points": {
                    "type": "integer",
                    "description": "Maximum number of key points to extract.",
                    "default": 5
                }
            },
            "required": ["text"]
        },
        function=_execute
    )

def search_document() -> Function:
    """
    Create a tool for searching within a document for specific information.
    
    Returns:
        Function: An ADK tool function for document search.
    """
    def _execute(document_text: str, query: str) -> Dict[str, Any]:
        """
        Search for specific information within a document.
        
        Args:
            document_text: The document content to search through
            query: The search query
            
        Returns:
            Dictionary containing the search results.
        """
        # Simple search implementation
        results = []
        paragraphs = document_text.split("\n\n")
        
        for i, para in enumerate(paragraphs):
            if query.lower() in para.lower():
                # Get context around the match
                start = max(0, i-1)
                end = min(len(paragraphs), i+2)
                context = "\n\n".join(paragraphs[start:end])
                results.append({
                    "context": context,
                    "relevance": "high" if query.lower() in para.lower() else "medium"
                })
                
                if len(results) >= 3:  # Limit to 3 results
                    break
        
        return {
            "results": results,
            "query": query,
            "total_matches": len(results)
        }
    
    return Function(
        name="search_document",
        description="Search for specific information within the provided document text.",
        parameters={
            "type": "object",
            "properties": {
                "document_text": {
                    "type": "string",
                    "description": "The document content to search through."
                },
                "query": {
                    "type": "string",
                    "description": "The search query or question to look for in the document."
                }
            },
            "required": ["document_text", "query"]
        },
        function=_execute
    )

def save_to_history() -> Function:
    """
    Create a tool for saving chat history to Firestore.
    
    Returns:
        Function: An ADK tool function for saving history.
    """
    def _execute(user_id: str, session_id: str, messages: List[Dict[str, str]]) -> Dict[str, bool]:
        """
        Save chat history to Firestore.
        
        Args:
            user_id: The user ID
            session_id: The session ID
            messages: The list of chat messages
            
        Returns:
            Dictionary indicating success or failure.
        """
        try:
            # Use the Firebase utils to save the history
            history_ref = fb_utils.db.collection('users').document(user_id) \
                .collection('chat_history').document(session_id)
            
            history_ref.set({
                'messages': messages,
                'updated_at': fb_utils.firestore.SERVER_TIMESTAMP
            }, merge=True)
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return Function(
        name="save_to_history",
        description="Save the conversation history to the user's account.",
        parameters={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID to save history for."
                },
                "session_id": {
                    "type": "string",
                    "description": "The session ID for this conversation."
                },
                "messages": {
                    "type": "array",
                    "description": "The list of messages in the conversation.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {
                                "type": "string",
                                "description": "The role of the message sender (user or assistant)."
                            },
                            "content": {
                                "type": "string",
                                "description": "The content of the message."
                            }
                        }
                    }
                }
            },
            "required": ["user_id", "session_id", "messages"]
        },
        function=_execute
    )

# Collect all tools into a single function for easy access
def get_all_tools() -> List[Function]:
    """
    Get all available tools for the agent.
    
    Returns:
        List[Function]: A list of all available tool functions.
    """
    return [
        proofread_text(),
        summarize_document(),
        extract_key_points(),
        search_document(),
        save_to_history(),
    ]