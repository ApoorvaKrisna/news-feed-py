from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SearchIntent(str, Enum):
    """Enumeration of search intents identified by LLM"""
    CATEGORY = "category"
    SCORE = "score"
    SEARCH = "search"
    SOURCE = "source"
    NEARBY = "nearby"
    GENERAL = "general"

class QueryRequest(BaseModel):
    """Request model for intelligent query processing"""
    query: str = Field(..., min_length=1, description="User's natural language query")
    user_lat: Optional[float] = Field(None, ge=-90.0, le=90.0, description="User's latitude")
    user_lon: Optional[float] = Field(None, ge=-180.0, le=180.0, description="User's longitude")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of results")
    include_summary: bool = Field(True, description="Whether to include LLM-generated summaries")

class CategoryRequest(BaseModel):
    """Request model for category-based search"""
    category: str = Field(..., description="News category to search for")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")

class ScoreRequest(BaseModel):
    """Request model for score-based search"""
    min_score: float = Field(0.7, ge=0.0, le=1.0, description="Minimum relevance score")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")

class SearchRequest(BaseModel):
    """Request model for text search"""
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    include_description: bool = Field(True, description="Whether to search in descriptions")

class SourceRequest(BaseModel):
    """Request model for source-based search"""
    source: str = Field(..., description="News source name")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")

class NearbyRequest(BaseModel):
    """Request model for location-based search"""
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude")
    radius: float = Field(10.0, ge=0.1, le=100.0, description="Search radius in kilometers")
    limit: int = Field(5, ge=1, le=50, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")

class TrendingRequest(BaseModel):
    """Request model for trending news"""
    lat: float = Field(..., ge=-90.0, le=90.0, description="User's latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="User's longitude")
    radius: float = Field(10.0, ge=0.1, le=100.0, description="Search radius in kilometers")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")
    hours_back: int = Field(24, ge=1, le=168, description="Hours to look back for trending calculation")

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class SuccessResponse(BaseModel):
    """Standard success response model"""
    success: bool = Field(True, description="Success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class PaginationInfo(BaseModel):
    """Pagination information model"""
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")
    total_items: int = Field(0, ge=0, description="Total number of items")
    total_pages: int = Field(0, ge=0, description="Total number of pages")
    has_next: bool = Field(False, description="Whether there are more pages")
    has_previous: bool = Field(False, description="Whether there are previous pages")

class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Health status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")

class QueryInfo(BaseModel):
    """Information about processed query"""
    original_query: str = Field(..., description="Original user query")
    processed_query: Optional[str] = Field(None, description="Processed query terms")
    intent: Optional[str] = Field(None, description="Detected search intent")
    entities: Optional[List[str]] = Field(None, description="Extracted entities")
    location_used: Optional[Dict[str, float]] = Field(None, description="Location coordinates used")
    processing_time_ms: Optional[float] = Field(None, description="Query processing time in milliseconds")