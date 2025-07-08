"""
Questions API - Provides suggested questions for the frontend
This is a placeholder implementation that will be enhanced with Azure models later
"""
from fastapi import APIRouter, Query
from typing import List, Dict, Optional
import random

router = APIRouter()

# Sample questions for different contexts
SAMPLE_QUESTIONS = {
    "general": [
        "What did I save about machine learning?",
        "Show me all videos I watched this week",
        "Find articles about Python programming",
        "What are my notes on productivity?",
        "Show me content tagged with 'tutorial'",
        "Find all YouTube videos in my library",
        "What did I save yesterday?",
        "Search for content about AI",
    ],
    "empty": [
        "How do I save a YouTube video?",
        "What types of content can I save?",
        "How do I organize my content with tags?",
        "Can I search through video transcripts?",
        "How do I export my data?",
    ],
    "contextual": [
        "Show me similar content",
        "What else did I save from this source?",
        "Find related videos",
        "What are the key points from this?",
        "Summarize this content",
    ]
}

@router.get("/suggest-questions")
async def suggest_questions(
    context: Optional[str] = Query(None, description="Context for questions (general, empty, contextual)"),
    limit: int = Query(5, ge=1, le=10, description="Number of questions to return")
):
    """
    Get suggested questions based on context.
    
    This is a placeholder that returns static questions.
    In the future, this will use Azure AI models to generate contextual questions.
    """
    context = context or "general"
    
    # Get questions for the specified context, fallback to general
    questions_pool = SAMPLE_QUESTIONS.get(context, SAMPLE_QUESTIONS["general"])
    
    # Randomly select questions up to the limit
    selected_questions = random.sample(
        questions_pool, 
        min(limit, len(questions_pool))
    )
    
    return {
        "questions": selected_questions,
        "context": context,
        "source": "static"  # Will be "ai-generated" when Azure models are integrated
    }

@router.get("/v1/suggest-questions")
async def suggest_questions_v1(
    context: Optional[str] = Query(None, description="Context for questions"),
    item_id: Optional[str] = Query(None, description="Item ID for contextual questions"),
    limit: int = Query(5, ge=1, le=10, description="Number of questions to return")
):
    """
    Version 1 endpoint for backward compatibility.
    Redirects to the main suggest-questions endpoint.
    """
    return await suggest_questions(context=context, limit=limit)