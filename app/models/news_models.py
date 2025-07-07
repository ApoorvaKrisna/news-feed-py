from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class NewsCategory(str, Enum):
    """Enumeration of common news categories based on actual data"""
    NATIONAL = "national"
    SPORTS = "sports"
    GENERAL = "General"
    WORLD = "world"
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    POLITICS = "politics"
    IPL_2025 = "IPL*2025"
    TECHNOLOGY = "technology"
    HEALTH_FITNESS = "Health___Fitness"
    STARTUP = "startup"
    IPL = "IPL"
    SCIENCE = "science"
    FINANCE = "FINANCE"
    CRICKET = "cricket"
    HATKE = "hatke"
    EDUCATION = "education"
    RUSSIA_UKRAINE = "Russia-Ukraine*Conflict"
    EXPLAINERS = "EXPLAINERS"


class NewsArticle(BaseModel):
    """Model for news articles stored in MongoDB"""
    id: str = Field(..., description="Unique article identifier (UUID)")
    title: str = Field(..., description="Article title")
    description: str = Field(..., description="Article description")
    url: str = Field(..., description="Article URL")
    publication_date: str = Field(..., description="Publication date as ISO string")
    source_name: str = Field(..., description="News source name")
    category: List[str] = Field(..., description="Article categories")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score between 0 and 1")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")

    @validator('publication_date')
    def validate_publication_date(cls, v):
        """Validate publication date format"""
        try:
            # Ensure it's a valid ISO format string
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Publication date must be a valid ISO format string')

    @validator('relevance_score')
    def validate_relevance_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Relevance score must be between 0 and 1')
        return v

    @validator('category')
    def validate_category(cls, v):
        if not v:
            raise ValueError('At least one category must be provided')
        return v

    @property
    def publication_datetime(self) -> datetime:
        """Convert publication_date string to datetime object"""
        return datetime.fromisoformat(self.publication_date.replace('Z', '+00:00'))


class EnrichedNewsArticle(NewsArticle):
    """Enhanced news article with LLM-generated content"""
    llm_summary: Optional[str] = Field(None, description="LLM-generated summary")
    distance_km: Optional[float] = Field(None, description="Distance from user location in km")
    text_match_score: Optional[float] = Field(None, description="Text matching score for search queries")
    trending_score: Optional[float] = Field(None, description="Trending score based on user interactions")


class NewsArticleResponse(BaseModel):
    """Response model for news articles API"""
    articles: List[EnrichedNewsArticle]
    total_count: int = Field(..., description="Total number of articles matching the query")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(10, description="Number of articles per page")
    query_info: Optional[Dict[str, Any]] = Field(None, description="Information about the query processed")


class UserEvent(BaseModel):
    """Model for simulated user interaction events"""
    user_id: str = Field(..., description="Unique user identifier")
    article_id: str = Field(..., description="Article identifier")
    event_type: str = Field(..., description="Type of event (view, click, share)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    user_latitude: float = Field(..., ge=-90.0, le=90.0, description="User's latitude")
    user_longitude: float = Field(..., ge=-180.0, le=180.0, description="User's longitude")
    session_id: Optional[str] = Field(None, description="User session identifier")

    @validator('event_type')
    def validate_event_type(cls, v):
        allowed_types = ['view', 'click', 'share', 'like', 'comment']
        if v not in allowed_types:
            raise ValueError(f'Event type must be one of: {allowed_types}')
        return v


class TrendingArticle(BaseModel):
    """Model for trending articles with computed scores"""
    article: EnrichedNewsArticle
    trending_score: float = Field(..., description="Computed trending score")
    interaction_count: int = Field(..., description="Number of interactions")
    unique_users: int = Field(..., description="Number of unique users who interacted")
    recent_interactions: int = Field(..., description="Interactions in the last 24 hours")


class LocationCluster(BaseModel):
    """Model for location-based clustering for caching"""
    cluster_id: str = Field(..., description="Unique cluster identifier")
    center_latitude: float = Field(..., ge=-90.0, le=90.0, description="Cluster center latitude")
    center_longitude: float = Field(..., ge=-180.0, le=180.0, description="Cluster center longitude")
    radius_km: float = Field(..., description="Cluster radius in kilometers")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    cached_articles: List[str] = Field(default_factory=list, description="Cached article IDs")


# Database document models (for MongoDB operations)
class NewsArticleDocument(BaseModel):
    """Document model for MongoDB operations - matches actual DB structure"""
    id: str = Field(..., description="UUID identifier")
    title: str
    description: str
    url: str
    publication_date: str  # ISO string format
    source_name: str
    category: List[str]
    relevance_score: float
    latitude: float
    longitude: float

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_news_article(self) -> NewsArticle:
        """Convert to NewsArticle model"""
        return NewsArticle(**self.dict())


class UserEventDocument(BaseModel):
    """Document model for user events in MongoDB"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    article_id: str
    event_type: str
    timestamp: datetime
    user_latitude: float
    user_longitude: float
    session_id: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }