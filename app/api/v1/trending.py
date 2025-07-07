from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Dict, Any, Annotated
from loguru import logger

from app.models.news_models import TrendingArticle
from app.models.api_models import TrendingRequest, SuccessResponse
from app.services.trending_service import TrendingService
from app.api.dependencies import (
    get_trending_service, validate_location_params, validate_radius_param,
    validate_hours_back_param, check_rate_limit
)
from app.utils.helpers import create_error_response, create_success_response

router = APIRouter(prefix="/trending", tags=["trending"])


@router.get(
    "/",
    response_model=List[TrendingArticle],
    summary="Get Trending Articles",
    description="Retrieve trending articles based on user interactions near a location"
)
async def get_trending_articles(
        request: Request,
        location: tuple[float, float] = Depends(validate_location_params),
        radius: float = Depends(validate_radius_param),
        hours_back: int = Depends(validate_hours_back_param),
        limit: Annotated[int, Query(ge=1, le=50, description="Number of trending articles")] = 10,
        trending_service: TrendingService = Depends(get_trending_service)
):
    """
    Get trending articles based on user interactions within a geographic area.

    The trending score is calculated based on:
    - Volume of user interactions (views, clicks, shares, etc.)
    - Recency of interactions
    - Geographic proximity to the user
    - Uniqueness of users (viral factor)
    """
    try:
        await check_rate_limit(request)

        lat, lon = location

        trending_articles = await trending_service.get_trending_articles(
            user_lat=lat,
            user_lon=lon,
            radius=radius,
            limit=limit,
            hours_back=hours_back
        )

        logger.info(f"Trending search: ({lat}, {lon}) radius={radius}km -> {len(trending_articles)} results")
        return trending_articles

    except Exception as e:
        logger.error(f"Error simulating user interactions: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("simulation_error", str(e))
        )


@router.post(
    "/interaction",
    response_model=SuccessResponse,
    summary="Record User Interaction",
    description="Record a real user interaction event with an article"
)
async def record_user_interaction(
        request: Request,
        user_id: Annotated[str, Query(min_length=1, max_length=50, description="User identifier")],
        article_id: Annotated[str, Query(min_length=36, max_length=36, description="Article UUID")],
        event_type: Annotated[str, Query(description="Type of interaction")],
        location: tuple[float, float] = Depends(validate_location_params),
        session_id: Annotated[str, Query(min_length=1, max_length=50, description="Session identifier")] = None,
        trending_service: TrendingService = Depends(get_trending_service)
):
    """
    Record a user interaction event with an article.

    Event types: view, click, share, like, comment
    """
    try:
        await check_rate_limit(request)

        # Validate event type
        valid_event_types = ["view", "click", "share", "like", "comment"]
        if event_type not in valid_event_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type. Valid types: {', '.join(valid_event_types)}"
            )

        # Validate article ID format (basic UUID check)
        if len(article_id) != 36 or article_id.count('-') != 4:
            raise HTTPException(
                status_code=400,
                detail="Invalid article ID format. Must be a valid UUID."
            )

        lat, lon = location

        success = await trending_service.record_user_interaction(
            user_id=user_id,
            article_id=article_id,
            event_type=event_type,
            user_lat=lat,
            user_lon=lon,
            session_id=session_id
        )

        if success:
            logger.info(f"Recorded {event_type} interaction: user={user_id}, article={article_id}")
            return SuccessResponse(
                message=f"Successfully recorded {event_type} interaction",
                data={
                    "user_id": user_id,
                    "article_id": article_id,
                    "event_type": event_type,
                    "location": {"lat": lat, "lon": lon}
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to record user interaction"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording user interaction: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("interaction_recording_error", str(e))
        )


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get User Activity Statistics",
    description="Get statistics about user activity and engagement"
)
async def get_user_activity_stats(
        request: Request,
        hours_back: int = Depends(validate_hours_back_param),
        trending_service: TrendingService = Depends(get_trending_service)
):
    """
    Get user activity statistics for the specified time period.

    Returns metrics like:
    - Total events
    - Unique users
    - Unique articles
    - Event type breakdown
    """
    try:
        await check_rate_limit(request)

        stats = await trending_service.get_user_activity_stats(hours_back=hours_back)

        logger.info(f"Retrieved user activity stats for {hours_back} hours")
        return stats

    except Exception as e:
        logger.error(f"Error getting user activity stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("stats_error", str(e))
        )


@router.delete(
    "/cleanup",
    response_model=SuccessResponse,
    summary="Cleanup Old Events",
    description="Clean up old user interaction events to manage database size"
)
async def cleanup_old_events(
        request: Request,
        days_to_keep: Annotated[int, Query(ge=1, le=30, description="Days of events to keep")] = 7,
        trending_service: TrendingService = Depends(get_trending_service)
):
    """
    Clean up old user interaction events.
    This helps manage database size by removing old engagement data.

    WARNING: This permanently deletes old interaction data.
    """
    try:
        await check_rate_limit(request)

        deleted_count = await trending_service.cleanup_old_events(days_to_keep=days_to_keep)

        logger.info(f"Cleaned up {deleted_count} old user interaction events")

        return SuccessResponse(
            message=f"Successfully cleaned up {deleted_count} old events",
            data={
                "deleted_count": deleted_count,
                "days_kept": days_to_keep
            }
        )

    except Exception as e:
        logger.error(f"Error cleaning up old events: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("cleanup_error", str(e))
        )
        error(f"Error getting trending articles: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("trending_error", str(e))
        )


@router.get(
    "/clustered",
    response_model=List[TrendingArticle],
    summary="Get Clustered Trending Articles",
    description="Get trending articles using location clustering for better cache performance"
)
async def get_clustered_trending_articles(
        request: Request,
        location: tuple[float, float] = Depends(validate_location_params),
        cluster_size: Annotated[float, Query(ge=1.0, le=20.0, description="Cluster size in km")] = 5.0,
        limit: Annotated[int, Query(ge=1, le=50, description="Number of trending articles")] = 10,
        trending_service: TrendingService = Depends(get_trending_service)
):
    """
    Get trending articles using geographic clustering for improved caching.
    This endpoint groups nearby locations into clusters to improve performance.
    """
    try:
        await check_rate_limit(request)

        lat, lon = location

        trending_articles = await trending_service.get_trending_by_location_clusters(
            lat=lat,
            lon=lon,
            cluster_size=cluster_size,
            limit=limit
        )

        logger.info(
            f"Clustered trending search: ({lat}, {lon}) cluster={cluster_size}km -> {len(trending_articles)} results")
        return trending_articles

    except Exception as e:
        logger.error(f"Error getting clustered trending articles: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("clustered_trending_error", str(e))
        )


@router.get(
    "/region",
    response_model=List[TrendingArticle],
    summary="Get Popular Articles by Region",
    description="Get popular articles within a geographic bounding box"
)
async def get_popular_articles_by_region(
        request: Request,
        min_lat: Annotated[float, Query(ge=-90.0, le=90.0, description="Minimum latitude")],
        max_lat: Annotated[float, Query(ge=-90.0, le=90.0, description="Maximum latitude")],
        min_lon: Annotated[float, Query(ge=-180.0, le=180.0, description="Minimum longitude")],
        max_lon: Annotated[float, Query(ge=-180.0, le=180.0, description="Maximum longitude")],
        hours_back: int = Depends(validate_hours_back_param),
        limit: Annotated[int, Query(ge=1, le=50, description="Number of articles")] = 10,
        trending_service: TrendingService = Depends(get_trending_service)
):
    """
    Get popular articles within a rectangular geographic region.
    Useful for analyzing trends in specific areas like cities or states.
    """
    try:
        await check_rate_limit(request)

        # Validate bounding box
        if min_lat >= max_lat:
            raise HTTPException(
                status_code=400,
                detail="min_lat must be less than max_lat"
            )

        if min_lon >= max_lon:
            raise HTTPException(
                status_code=400,
                detail="min_lon must be less than max_lon"
            )

        trending_articles = await trending_service.get_popular_articles_by_region(
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon,
            hours_back=hours_back,
            limit=limit
        )

        logger.info(
            f"Region trending: bbox({min_lat},{min_lon})-({max_lat},{max_lon}) -> {len(trending_articles)} results")
        return trending_articles

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting popular articles by region: {e}")
        raise HTTPException(
            status_code=500,
            detail=create_error_response("region_trending_error", str(e))
        )


@router.post(
    "/simulate",
    response_model=SuccessResponse,
    summary="Simulate User Interactions",
    description="Generate simulated user interaction events for testing trending functionality"
)
async def simulate_user_interactions(
        request: Request,
        num_events: Annotated[int, Query(ge=10, le=1000, description="Number of events to simulate")] = 100,
        location_radius: Annotated[float, Query(ge=1.0, le=100.0, description="Geographic spread in km")] = 50.0,
        trending_service: TrendingService = Depends(get_trending_service)
):
    """
    Simulate user interaction events for testing the trending functionality.
    This creates realistic user engagement data with articles.

    WARNING: This is for testing/demo purposes only.
    """
    try:
        await check_rate_limit(request)

        events_created = await trending_service.simulate_user_interactions(
            num_events=num_events,
            location_radius=location_radius
        )

        logger.info(f"Simulated {events_created} user interaction events")

        return SuccessResponse(
            message=f"Successfully simulated {events_created} user interaction events",
            data={
                "events_created": events_created,
                "requested_events": num_events,
                "location_radius_km": location_radius
            }
        )

    except Exception as e:
        logger.error(f"Error simulating user interactions: {e}")