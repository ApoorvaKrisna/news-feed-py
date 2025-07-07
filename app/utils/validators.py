import re
from typing import List, Optional, Tuple
from datetime import datetime


def validate_search_query(query: str) -> Tuple[bool, Optional[str]]:
    """Validate search query input"""
    if not query:
        return False, "Query cannot be empty"

    if len(query.strip()) < 1:
        return False, "Query must contain at least one character"

    if len(query) > 500:
        return False, "Query cannot exceed 500 characters"

    return True, None


def validate_coordinates(lat: float, lon: float) -> Tuple[bool, Optional[str]]:
    """Validate latitude and longitude coordinates"""
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False, "Coordinates must be numeric values"

    if not (-90.0 <= lat <= 90.0):
        return False, "Latitude must be between -90 and 90 degrees"

    if not (-180.0 <= lon <= 180.0):
        return False, "Longitude must be between -180 and 180 degrees"

    return True, None


def validate_radius(radius: float, max_radius: float = 100.0) -> Tuple[bool, Optional[str]]:
    """Validate search radius"""
    if not isinstance(radius, (int, float)):
        return False, "Radius must be a numeric value"

    if radius <= 0:
        return False, "Radius must be greater than 0"

    if radius > max_radius:
        return False, f"Radius cannot exceed {max_radius} km"

    return True, None


def validate_limit_parameter(limit: int, max_limit: int = 50) -> Tuple[bool, Optional[str]]:
    """Validate limit parameter for API requests"""
    if not isinstance(limit, int):
        return False, "Limit must be an integer"

    if limit < 1:
        return False, "Limit must be at least 1"

    if limit > max_limit:
        return False, f"Limit cannot exceed {max_limit}"

    return True, None


def validate_offset_parameter(offset: int) -> Tuple[bool, Optional[str]]:
    """Validate offset parameter for pagination"""
    if not isinstance(offset, int):
        return False, "Offset must be an integer"

    if offset < 0:
        return False, "Offset cannot be negative"

    if offset > 10000:
        return False, "Offset cannot exceed 10000"

    return True, None


def validate_relevance_score(score: float) -> Tuple[bool, Optional[str]]:
    """Validate relevance score"""
    if not isinstance(score, (int, float)):
        return False, "Relevance score must be a numeric value"

    if not (0.0 <= score <= 1.0):
        return False, "Relevance score must be between 0.0 and 1.0"

    return True, None


def validate_source(source: str) -> Tuple[bool, Optional[str]]:
    """Validate news source"""
    if not source:
        return False, "Source cannot be empty"

    if len(source.strip()) == 0:
        return False, "Source cannot be empty"

    if len(source) > 100:
        return False, "Source name cannot exceed 100 characters"

    return True, None


def validate_time_range(hours_back: int, max_hours: int = 168) -> Tuple[bool, Optional[str]]:
    """Validate time range for trending queries"""
    if not isinstance(hours_back, int):
        return False, "Hours back must be an integer"

    if hours_back < 1:
        return False, "Hours back must be at least 1"

    if hours_back > max_hours:
        return False, f"Hours back cannot exceed {max_hours} hours (1 week)"

    return True, None


def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> Tuple[bool, Optional[str]]:
    """Validate pagination parameters"""
    if not isinstance(page, int) or page < 1:
        return False, "Page number must be a positive integer"

    if not isinstance(page_size, int) or page_size < 1:
        return False, "Page size must be a positive integer"

    if page_size > max_page_size:
        return False, f"Page size cannot exceed {max_page_size}"

    return True, None


def validate_category(category: str, available_categories: List[str]) -> Tuple[bool, Optional[str]]:
    """Validate news category"""
    if not category:
        return False, "Category cannot be empty"

    return True, None


def validate_query_request(query: str, lat: Optional[float] = None,
                           lon: Optional[float] = None, limit: int = 5) -> List[str]:
    """Validate parameters for query request"""
    errors = []

    is_valid, error = validate_search_query(query)
    if not is_valid:
        errors.append(f"Query validation: {error}")

    if lat is not None and lon is not None:
        is_valid, error = validate_coordinates(lat, lon)
        if not is_valid:
            errors.append(f"Coordinates validation: {error}")

    is_valid, error = validate_limit_parameter(limit)
    if not is_valid:
        errors.append(f"Limit validation: {error}")

    return errors


def validate_nearby_request(lat: float, lon: float, radius: float = 10.0,
                            limit: int = 5) -> List[str]:
    """Validate parameters for nearby request"""
    errors = []

    is_valid, error = validate_coordinates(lat, lon)
    if not is_valid:
        errors.append(f"Coordinates validation: {error}")

    is_valid, error = validate_radius(radius)
    if not is_valid:
        errors.append(f"Radius validation: {error}")

    is_valid, error = validate_limit_parameter(limit)
    if not is_valid:
        errors.append(f"Limit validation: {error}")

    return errors


def validate_trending_request(lat: float, lon: float, radius: float = 10.0,
                              limit: int = 10, hours_back: int = 24) -> List[str]:
    """Validate parameters for trending request"""
    errors = []

    is_valid, error = validate_coordinates(lat, lon)
    if not is_valid:
        errors.append(f"Coordinates validation: {error}")

    is_valid, error = validate_radius(radius)
    if not is_valid:
        errors.append(f"Radius validation: {error}")

    is_valid, error = validate_limit_parameter(limit)
    if not is_valid:
        errors.append(f"Limit validation: {error}")

    is_valid, error = validate_time_range(hours_back)
    if not is_valid:
        errors.append(f"Time range validation: {error}")

    return errors


class ValidationError(Exception):
    """Custom exception for validation errors"""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)