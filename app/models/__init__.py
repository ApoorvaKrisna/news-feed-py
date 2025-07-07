"""Data models for the contextual news retrieval system"""

from .news_models import (
    NewsCategory,
    NewsArticle, 
    EnrichedNewsArticle, 
    NewsArticleResponse,
    UserEvent,
    TrendingArticle,
    LocationCluster,
    NewsArticleDocument,
    UserEventDocument
)

from .api_models import (
    SearchIntent,
    QueryRequest,
    CategoryRequest,
    ScoreRequest,
    SearchRequest,
    SourceRequest,
    NearbyRequest,
    TrendingRequest,
    ErrorResponse,
    SuccessResponse,
    PaginationInfo,
    HealthCheckResponse,
    QueryInfo
)

from .llm_models import (
    LLMIntent,
    ExtractedEntity,
    LLMAnalysis,
    SummaryRequest,
    SummaryResponse,
    LLMError,
    QueryProcessingRequest,
    QueryProcessingResponse,
    LLMPrompts
)
