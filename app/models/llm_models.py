from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum


class LLMIntent(str, Enum):
    """Enumeration of search intents that can be identified by LLM"""
    CATEGORY = "category"
    SCORE = "score"
    SEARCH = "search"
    SOURCE = "source"
    NEARBY = "nearby"
    GENERAL = "general"
    TRENDING = "trending"


class ExtractedEntity(BaseModel):
    """Model for entities extracted by LLM"""
    text: str = Field(..., description="The extracted entity text")
    type: str = Field(..., description="Type of entity (person, organization, location, event)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class LLMAnalysis(BaseModel):
    """Model for LLM analysis of user query"""
    original_query: str = Field(..., description="Original user query")
    intent: LLMIntent = Field(..., description="Identified search intent")
    entities: List[ExtractedEntity] = Field(default_factory=list, description="Extracted entities")
    keywords: List[str] = Field(default_factory=list, description="Key search terms")
    location_mentioned: Optional[str] = Field(None, description="Location mentioned in query")
    category_mentioned: Optional[str] = Field(None, description="Category mentioned in query")
    source_mentioned: Optional[str] = Field(None, description="Source mentioned in query")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall analysis confidence")
    reasoning: str = Field(..., description="LLM reasoning for the analysis")


class SummaryRequest(BaseModel):
    """Request model for LLM summary generation"""
    title: str = Field(..., description="Article title")
    description: str = Field(..., description="Article description")
    url: Optional[str] = Field(None, description="Article URL for context")
    max_length: int = Field(150, ge=50, le=500, description="Maximum summary length")


class SummaryResponse(BaseModel):
    """Response model for LLM-generated summary"""
    summary: str = Field(..., description="Generated summary")
    key_points: List[str] = Field(default_factory=list, description="Key points extracted")
    sentiment: Optional[str] = Field(None, description="Article sentiment")
    topics: List[str] = Field(default_factory=list, description="Main topics covered")


class LLMError(BaseModel):
    """Model for LLM service errors"""
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    query: Optional[str] = Field(None, description="Query that caused the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class QueryProcessingRequest(BaseModel):
    """Request model for intelligent query processing"""
    query: str = Field(..., min_length=1, description="User's natural language query")
    user_location: Optional[Dict[str, float]] = Field(None, description="User's lat/lon coordinates")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class QueryProcessingResponse(BaseModel):
    """Response model for query processing"""
    analysis: LLMAnalysis = Field(..., description="LLM analysis results")
    suggested_endpoint: str = Field(..., description="Recommended API endpoint")
    query_parameters: Dict[str, Any] = Field(..., description="Parameters for the endpoint")
    fallback_strategy: Optional[str] = Field(None, description="Fallback if primary strategy fails")


# Prompt templates for LLM interactions
class LLMPrompts:
    """Container for LLM prompt templates"""

    ENTITY_EXTRACTION = """
    Analyze the following news query and extract relevant entities and determine the user's search intent.

    Query: "{query}"

    Identify:
    1. Intent (category, score, search, source, nearby, general)
    2. Entities (people, organizations, locations, events)
    3. Keywords for search
    4. Any mentioned category, source, or location

    Respond in JSON format with the structure:
    {{
        "intent": "category|score|search|source|nearby|general",
        "entities": [
            {{"text": "entity", "type": "person|organization|location|event", "confidence": 0.95}}
        ],
        "keywords": ["keyword1", "keyword2"],
        "location_mentioned": "location or null",
        "category_mentioned": "category or null", 
        "source_mentioned": "source or null",
        "confidence": 0.85,
        "reasoning": "explanation of analysis"
    }}

    Categories available: national, sports, General, world, business, entertainment, politics, IPL*2025, technology, Health___Fitness, startup, IPL, science, FINANCE, cricket, hatke, education, Russia-Ukraine*Conflict, EXPLAINERS

    Common sources: Hindustan Times, Free Press Journal, News Karnataka, News18, ET Now, The Indian Express, Moneycontrol, Youtube, Reuters, Times Now, PTI, ANI
    """

    SUMMARY_GENERATION = """
    Create a concise, informative summary of this news article.

    Title: {title}
    Description: {description}

    Requirements:
    - Maximum {max_length} characters
    - Focus on key facts and main points
    - Maintain objective tone
    - Include important details like who, what, when, where

    Also identify:
    - 2-3 key points
    - Overall sentiment (positive, negative, neutral)
    - Main topics/themes

    Respond in JSON format:
    {{
        "summary": "concise summary text",
        "key_points": ["point 1", "point 2", "point 3"],
        "sentiment": "positive|negative|neutral",
        "topics": ["topic1", "topic2"]
    }}
    """

    INTENT_CLASSIFICATION = """
    Classify the search intent for this news query:

    Query: "{query}"
    User Location: {user_location}

    Intent types:
    - category: User wants news from specific category
    - source: User wants news from specific source
    - search: User wants to search for specific terms
    - score: User wants high-quality/relevant articles
    - nearby: User wants location-based news
    - general: General news request

    Respond with the most appropriate intent and confidence level (0-1).

    JSON format:
    {{
        "intent": "intent_type",
        "confidence": 0.95,
        "reasoning": "why this intent was chosen"
    }}
    """