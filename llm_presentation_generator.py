"""
LLM-Based Presentation Generator

This module creates PowerPoint presentations from topics using LLM-generated structured content.
It handles the entire workflow from prompt engineering to presentation creation.
"""

import os
import tempfile
import uuid
from io import BytesIO
import re

from presentation_builder import generate_presentation_from_text, parse_presentation_content

def generate_presentation_from_topic(topic, model, tone="professional"):
    """
    Generate a complete presentation from a topic using an LLM to structure the content.
    
    Args:
        topic (str): The presentation topic/subject
        model: The LLM model to use for content generation
        tone (str): Presentation style ("professional", "academic", "casual")
      Returns:
        tuple: (presentation_path, presentation_filename)
    """
    
    if not model:
        raise ValueError("A valid LLM model must be provided for topic-based presentation generation")
        
    try:
        # Engineer a detailed prompt to get structured content from the LLM
        # Make sure we're directly addressing the user's requested topic
        clean_topic = topic.strip()
        print(f"Creating presentation on specific topic: '{clean_topic}'")
        
        prompt = f"""
        Create a comprehensive presentation specifically about: "{clean_topic}"
        
        IMPORTANT: The presentation MUST be all about "{clean_topic}" and only this topic. 
        Do NOT replace with a generic template or different subject.
        
        I need a detailed, well-structured presentation in Markdown format with specific factual content (not placeholders).
        
        Format your response exactly like this:
        
        # [Engaging Title for the Presentation about {clean_topic}]
        
        ## [Slide 1 Title]
        - [Specific bullet point with factual information about {clean_topic}]
        - [Another specific bullet point with data or important detail about {clean_topic}]
        - [Additional bullet point with concrete information about {clean_topic}]
        - [Another relevant specific point about {clean_topic}]
        - [Final bullet point for this slide about {clean_topic}]
        
        ## [Slide 2 Title]
        - [Specific bullet point about {clean_topic}]
        - [Another specific bullet point about {clean_topic}]
        - [etc...]
        
        REQUIREMENTS:
        1. Create 5-7 slides total, each with exactly 5 bullet points
        2. Each slide title should be clear and concise (5-7 words)
        3. Bullet points MUST be specific facts, statistics, or concrete insights - NEVER generic placeholders
        4. Include actual numbers, percentages, and data points when relevant
        5. Make sure content flows logically from introduction through main points to conclusion
        6. Content should be factually accurate and representative of current knowledge
        7. Use varied language and structures across slides
        8. The first slide should introduce the topic, and the last slide should provide a conclusion or next steps
        
        DO NOT use generic placeholders like "Discuss the impact..." or "Explore the benefits..."
        INSTEAD use specific content like "Reduces operational costs by 27% through automation"
        
        Be concise but informative in each bullet point.
        """

        # Get LLM response with robust error handling
        print(f"Generating presentation content for topic: {topic}")
        response = model.generate_content(prompt)
        
        # Extract the content from the response
        if not response or not hasattr(response, 'text') or not response.text:
            raise ValueError("LLM returned empty or invalid response")
        
        response_text = response.text
        
        # Parse the LLM-generated content into a structured format
        slides = parse_llm_presentation_content(response_text)
        
        # Generate title from the content if available, otherwise use the topic
        title = extract_title_from_content(response_text)
        
        # Make sure the title references the topic in some way
        if not title or not any(word.lower() in topic.lower() for word in title.split()):
            title = f"Presentation on {topic}"
          # Create presentation using the presentation builder
        return generate_presentation_from_text(response_text, None, title, tone)
    except Exception as e:
        print(f"Error generating presentation from topic: {e}")
        
        # Fallback to a simpler approach if the topic-specific generation fails
        try:
            print(f"Attempting fallback presentation generation for topic: {topic}")
            
            # Create a simpler markdown structure directly
            fallback_content = f"""
            # Presentation on {topic}
            
            ## Introduction to {topic}
            - Key information about {topic}
            - Background and context
            - Importance and relevance
            - Main areas of discussion
            - Goals of this presentation
            
            ## Key Facts about {topic}
            - Most important fact about {topic}
            - Second key point about {topic}
            - Historical or contextual information
            - Current state or status
            - Relevant statistics or figures
            
            ## Analysis of {topic}
            - Main components or aspects
            - Benefits or advantages
            - Challenges or limitations
            - Comparative analysis
            - Expert opinions or research findings
            
            ## Applications or Examples
            - Primary use case or example            - Alternative applications
            - Real-world implementations
            - Case study or illustration
            - Practical considerations
            
            ## Future Developments
            - Upcoming changes or innovations
            - Predicted trends
            - Areas for improvement
            - Research directions
            - Long-term outlook
            
            ## Conclusion
            - Summary of key points
            - Main takeaways
            - Recommendations
            - Final thoughts
            - Questions to consider
            """
            
            # Use the fallback content to create the presentation
            return generate_presentation_from_text(fallback_content, None, f"Presentation on {topic}", tone)
            
        except Exception as fallback_error:
            print(f"Fallback presentation generation also failed: {fallback_error}")
            raise


def parse_llm_presentation_content(text):
    """
    Parse the LLM-generated markdown content into structured slides.
    
    Args:
        text (str): Markdown-formatted text from LLM
        
    Returns:
        list: List of dictionaries with 'title' and 'bullets' keys
    """
    slides = []
    
    # First check if we have a markdown structure with # and ## headers
    main_title = None
    current_slide_title = None
    current_bullets = []
    
    for line in text.split('\n'):
        line = line.strip()
        
        # Check for main title
        if line.startswith('# '):
            main_title = line.replace('# ', '').strip()
            continue
            
        # Check for slide title
        if line.startswith('## '):
            # If we were working on a previous slide, save it
            if current_slide_title and current_bullets:
                slides.append({
                    'title': current_slide_title,
                    'bullets': current_bullets
                })
                current_bullets = []
                
            current_slide_title = line.replace('## ', '').strip()
            continue
            
        # Check for bullet points
        if line.startswith('- ') or line.startswith('* '):
            bullet_text = line[2:].strip()
            if bullet_text:
                current_bullets.append(bullet_text)
    
    # Don't forget to add the last slide
    if current_slide_title and current_bullets:
        slides.append({
            'title': current_slide_title,
            'bullets': current_bullets
        })
    
    return slides


def extract_title_from_content(text):
    """
    Extract the main title from the LLM-generated content.
    
    Args:
        text (str): Markdown-formatted text
        
    Returns:
        str: The main title or None if not found
    """
    # Look for the main title with # format
    title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()
    
    # If no main title found, look for the first line if it seems like a title
    lines = text.strip().split('\n')
    if lines and not lines[0].startswith(('#', '-', '*')):
        return lines[0].strip()
    
    return None
