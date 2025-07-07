from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional, Annotated
from loguru import logger

from app.models.news_models import NewsArticleResponse, EnrichedNewsArticle
from app.models.api_models import (
    QueryRequest, CategoryRequest, ScoreRequest, SearchRequest,
    SourceRequest, NearbyRequest, ErrorResponse, SuccessResponse
)
from app.services.news_service import NewsService
from app.api.dependencies import (
    get_news_service, validate_pagination_params, validate_location_params,
    validate_radius_param, validate_query_param, validate_source_param,
    validate_score_param, validate_category_param, validate_optional_location_params,
    create_validation_error_response, create_not_found_error_response,
    create_internal_error_response, check_rate_limit
)
from app.utils.helpers import create_error_response, create_success_response

router = APIRouter(prefix="/news", tags=["news"])


# Main intelligent query endpoint
@router.post(
    "/query",
    response_model=NewsArticleResponse,
    summary="Intelligent Query Processing",
    description="Process natural language queries using LLM to determine optimal search strategy"
)
async def intelligent_query(
        request: Request,
        query_request: QueryRequest,
        news_service: NewsService = Depends(get_news_service)
):
    """
    Process an intelligent query using LLM analysis to determine the best search strategy.

    The system will:
    1. Analyze the query using LLM to extract entities and intent
    2. Determine the optimal search strategy (category, source, nearby, etc.)
    3. Execute the search with appropriate ranking
    4. Enrich results with LLM-generated summaries
    """
    try:
        # Rate limiting check
        await check_rate_limit(request)

        # Process the intelligent query
        result = await news_service.intelligent_query(
            query=query_request.query,
            user_lat=query_request.user_lat,
            user_lon=query_request.user_lon,
            limit=query_request.limit,
            include_summary=query_request.include_summary
        )

        logger.info(f"Intelligent query processed: '{query_request.query}' -> {len(result.articles)} results")
        return result

    except ValueError as e:
        logger.warning(f"Validation error in intelligent query: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in intelligent query processing: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("processing_error", str(e))
        )


# Category-based search
@router.get(
    "/category",
    response_model=NewsArticleResponse,
    summary="Get Articles by Category",
    description="Retrieve articles from a specific category, sorted by publication date"
)
async def get_articles_by_category(
        request: Request,
        category: str = Depends(validate_category_param),
        pagination: tuple[int, int] = Depends(validate_pagination_params),
        news_service: NewsService = Depends(get_news_service)
):
    """
    Get articles by category with pagination.
    Results are sorted by publication date (most recent first).
    """
    try:
        await check_rate_limit(request)

        limit, offset = pagination
        result = await news_service.get_articles_by_category(category, limit, offset)

        logger.info(f"Category search: '{category}' -> {len(result.articles)} results")
        return result

    except Exception as e:
        logger.error(f"Error in category search: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("category_search_error", str(e))
        )


# Score-based search
@router.get(
    "/score",
    response_model=NewsArticleResponse,
    summary="Get High-Quality Articles",
    description="Retrieve articles with relevance score above a threshold, sorted by score"
)
async def get_articles_by_score(
        request: Request,
        min_score: float = Depends(validate_score_param),
        pagination: tuple[int, int] = Depends(validate_pagination_params),
        news_service: NewsService = Depends(get_news_service)
):
    """
    Get articles by minimum relevance score.
    Results are sorted by relevance score (highest first).
    """
    try:
        await check_rate_limit(request)

        limit, offset = pagination
        result = await news_service.get_articles_by_score(min_score, limit, offset)

        logger.info(f"Score search: min_score={min_score} -> {len(result.articles)} results")
        return result

    except Exception as e:
        logger.error(f"Error in score search: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("score_search_error", str(e))
        )


# Text search
@router.get(
    "/search",
    response_model=NewsArticleResponse,
    summary="Search Articles by Text",
    description="Search articles by text in title and description with relevance ranking"
)
async def search_articles(
        request: Request,
        query: str = Depends(validate_query_param),
        pagination: tuple[int, int] = Depends(validate_pagination_params),
        include_summaries: Annotated[bool, Query(description="Include LLM-generated summaries")] = False,
        news_service: NewsService = Depends(get_news_service)
):
    """
    Search articles by text query in title and description.
    Results are ranked by text matching score and relevance score.
    """
    try:
        await check_rate_limit(request)

        limit, offset = pagination
        result = await news_service.search_articles(
            query, limit, offset, include_summaries
        )

        logger.info(f"Text search: '{query}' -> {len(result.articles)} results")
        return result

    except Exception as e:
        logger.error(f"Error in text search: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("text_search_error", str(e))
        )


# Source-based search
@router.get(
    "/source",
    response_model=NewsArticleResponse,
    summary="Get Articles by Source",
    description="Retrieve articles from a specific news source, sorted by date"
)
async def get_articles_by_source(
        request: Request,
        source: str = Depends(validate_source_param),
        pagination: tuple[int, int] = Depends(validate_pagination_params),
        news_service: NewsService = Depends(get_news_service)
):
    """
    Get articles by news source.
    Results are sorted by publication date (most recent first).
    """
    try:
        await check_rate_limit(request)

        limit, offset = pagination
        result = await news_service.get_articles_by_source(source, limit, offset)

        logger.info(f"Source search: '{source}' -> {len(result.articles)} results")
        return result

    except Exception as e:
        logger.error(f"Error in source search: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("source_search_error", str(e))
        )


# Location-based search
@router.get(
    "/nearby",
    response_model=NewsArticleResponse,
    summary="Get Nearby Articles",
    description="Retrieve articles published within a radius of a location, sorted by distance"
)
async def get_nearby_articles(
        request: Request,
        location: tuple[float, float] = Depends(validate_location_params),
        radius: float = Depends(validate_radius_param),
        pagination: tuple[int, int] = Depends(validate_pagination_params),
        news_service: NewsService = Depends(get_news_service)
):
    """
    Get articles within a specified radius of a location.
    Results are sorted by distance (closest first) and include distance information.
    """
    try:
        await check_rate_limit(request)

        lat, lon = location
        limit, offset = pagination

        result = await news_service.get_nearby_articles(lat, lon, radius, limit, offset)

        logger.info(f"Nearby search: ({lat}, {lon}) radius={radius}km -> {len(result.articles)} results")
        return result

    except Exception as e:
        logger.error(f"Error in nearby search: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("nearby_search_error", str(e))
        )


# Utility endpoints
@router.get(
    "/categories",
    response_model=List[str],
    summary="Get Available Categories",
    description="Retrieve all available news categories"
)
async def get_available_categories(
        request: Request,
        news_service: NewsService = Depends(get_news_service)
):
    """Get all available news categories in the database."""
    try:
        await check_rate_limit(request)

        categories = await news_service.get_available_categories()
        logger.info(f"Retrieved {len(categories)} available categories")
        return categories

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("categories_error", str(e))
        )


@router.get(
    "/sources",
    response_model=List[str],
    summary="Get Available Sources",
    description="Retrieve all available news sources"
)
async def get_available_sources(
        request: Request,
        news_service: NewsService = Depends(get_news_service)
):
    """Get all available news sources in the database."""
    try:
        await check_rate_limit(request)

        sources = await news_service.get_available_sources()
        logger.info(f"Retrieved {len(sources)} available sources")
        return sources

    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("sources_error", str(e))
        )


@router.get(
    "/random",
    response_model=List[EnrichedNewsArticle],
    summary="Get Random Articles",
    description="Retrieve random articles for testing and exploration"
)
async def get_random_articles(
        request: Request,
        limit: Annotated[int, Query(ge=1, le=20, description="Number of random articles")] = 5,
        news_service: NewsService = Depends(get_news_service)
):
    """Get random articles for testing and exploration."""
    try:
        await check_rate_limit(request)

        articles = await news_service.get_random_articles(limit)
        logger.info(f"Retrieved {len(articles)} random articles")
        return articles

    except Exception as e:
        logger.error(f"Error getting random articles: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("random_articles_error", str(e))
        )


@router.get(
    "/{article_id}",
    response_model=EnrichedNewsArticle,
    summary="Get Article by ID",
    description="Retrieve a specific article by its ID"
)
async def get_article_by_id(
        request: Request,
        article_id: str,
        news_service: NewsService = Depends(get_news_service)
):
    """Get a specific article by its ID."""
    try:
        await check_rate_limit(request)

        # Basic UUID validation
        if len(article_id) != 36 or article_id.count('-') != 4:
            raise HTTPException(
                status_code=400,
                detail="Invalid article ID format. Must be a valid UUID."
            )

        article = await news_service.get_article_by_id(article_id)

        if not article:
            raise HTTPException(
                status_code=404,
                detail=f"Article with ID '{article_id}' not found"
            )

        logger.info(f"Retrieved article by ID: {article_id}")
        return article

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article by ID: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("article_retrieval_error", str(e))
        )