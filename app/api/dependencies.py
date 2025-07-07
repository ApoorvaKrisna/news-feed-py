from fastapi import HTTPException, Depends, Query
from typing import Optional, Annotated
from fastapi import HTTPException, Depends, Query
from typing import Optional, Annotated
from functools import lru_cache

from app.services.database import DatabaseService
from app.services.llm_service import LLMService
from app.services.news_service import NewsService
from app.services.trending_service import TrendingService
from app.utils.validators import (
    validate_coordinates, validate_radius, validate_limit_parameter,
    validate_offset_parameter, validate_search_query, validate_source,
    validate_relevance_score, validate_time_range
)


# Use the same database service instance from main.py
async def get_database_service() -> DatabaseService:
    """Get database service instance"""
    # Import here to avoid circular imports
    from app.main import db_service
    return db_service


async def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    # Import here to avoid circular imports
    from app.main import llm_service
    return llm_service


def get_news_service(
        db_service: DatabaseService = Depends(get_database_service),
        llm_service: LLMService = Depends(get_llm_service)
) -> NewsService:
    """Get news service instance"""
    return NewsService(db_service, llm_service)


def get_trending_service(
        db_service: DatabaseService = Depends(get_database_service)
) -> TrendingService:
    """Get trending service instance"""
    return TrendingService(db_service)


# Validation functions (simplified)
def validate_pagination_params(
        limit: Annotated[int, Query(ge=1, le=50)] = 5,
        offset: Annotated[int, Query(ge=0)] = 0
) -> tuple[int, int]:
    return limit, offset


def validate_location_params(
        lat: Annotated[float, Query(ge=-90.0, le=90.0)],
        lon: Annotated[float, Query(ge=-180.0, le=180.0)]
) -> tuple[float, float]:
    return lat, lon


def validate_radius_param(
        radius: Annotated[float, Query(ge=0.1, le=100.0)] = 10.0
) -> float:
    return radius


def validate_query_param(
        query: Annotated[str, Query(min_length=1, max_length=500)]
) -> str:
    return query.strip()


def validate_source_param(
        source: Annotated[str, Query(min_length=1, max_length=100)]
) -> str:
    return source.strip()


def validate_score_param(
        min_score: Annotated[float, Query(ge=0.0, le=1.0)] = 0.7
) -> float:
    return min_score


def validate_category_param(
        category: Annotated[str, Query(min_length=1)]
) -> str:
    return category.strip()


def validate_hours_back_param(
        hours_back: Annotated[int, Query(ge=1, le=168)] = 24
) -> int:
    return hours_back


def validate_optional_location_params(
        lat: Annotated[Optional[float], Query(ge=-90.0, le=90.0)] = None,
        lon: Annotated[Optional[float], Query(ge=-180.0, le=180.0)] = None
) -> tuple[Optional[float], Optional[float]]:
    return lat, lon


# Custom exception handlers
def create_validation_error_response(detail: str):
    """Create standardized validation error response"""
    return HTTPException(
        status_code=400,
        detail={
            "error": "validation_error",
            "message": detail,
            "timestamp": "2024-01-01T00:00:00Z"  # Will be updated by FastAPI
        }
    )


def create_not_found_error_response(resource: str, identifier: str = None):
    """Create standardized not found error response"""
    message = f"{resource} not found"
    if identifier:
        message += f" with identifier: {identifier}"

    return HTTPException(
        status_code=404,
        detail={
            "error": "not_found",
            "message": message,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


def create_internal_error_response(message: str = "Internal server error"):
    """Create standardized internal error response"""
    return HTTPException(
        status_code=500,
        detail={
            "error": "internal_error",
            "message": message,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


# Health check dependency
async def check_services_health(
        db_service: DatabaseService = Depends(get_database_service),
        llm_service: LLMService = Depends(get_llm_service)
) -> dict:
    """Check health of all services"""
    health_status = {
        "database": "unknown",
        "llm_service": "unknown"
    }

    try:
        await db_service.ping()
        health_status["database"] = "healthy"
    except Exception:
        health_status["database"] = "unhealthy"

    try:
        llm_healthy = await llm_service.health_check()
        health_status["llm_service"] = "healthy" if llm_healthy else "unhealthy"
    except Exception:
        health_status["llm_service"] = "unhealthy"

    return health_status


# Rate limiting dependency (basic implementation)
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio


class RateLimiter:
    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, client_ip: str) -> bool:
        async with self._lock:
            now = datetime.utcnow()
            window_start = now - timedelta(minutes=self.window_minutes)

            # Clean old requests
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > window_start
            ]

            # Check if under limit
            if len(self.requests[client_ip]) >= self.max_requests:
                return False

            # Add current request
            self.requests[client_ip].append(now)
            return True


# Simple rate limiting (basic implementation)
async def check_rate_limit(request):
    """Basic rate limiting check"""
    return True  # Simplified for now