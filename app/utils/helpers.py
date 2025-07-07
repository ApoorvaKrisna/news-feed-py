import math
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from loguru import logger


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    using the Haversine formula

    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees

    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Radius of Earth in kilometers
    R = 6371.0

    return R * c


def normalize_text(text: str) -> str:
    """
    Normalize text for better matching and search

    Args:
        text: Input text to normalize

    Returns:
        Normalized text
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove special characters but keep alphanumeric, spaces, and basic punctuation
    text = re.sub(r'[^\w\s\-_.,!?]', '', text)

    return text


def extract_keywords(text: str, min_length: int = 3, max_words: int = 10) -> List[str]:
    """
    Extract keywords from text for search purposes

    Args:
        text: Input text
        min_length: Minimum length of keywords
        max_words: Maximum number of keywords to return

    Returns:
        List of keywords
    """
    if not text:
        return []

    # Normalize text
    normalized = normalize_text(text)

    # Split into words
    words = normalized.split()

    # Filter out common stop words and short words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
        'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }

    keywords = []
    for word in words:
        if (len(word) >= min_length and
                word not in stop_words and
                word.isalpha()):  # Only alphabetic words
            keywords.append(word)

    # Remove duplicates while preserving order
    unique_keywords = []
    seen = set()
    for keyword in keywords:
        if keyword not in seen:
            unique_keywords.append(keyword)
            seen.add(keyword)

    return unique_keywords[:max_words]


def parse_iso_datetime(iso_string: str) -> datetime:
    """
    Parse ISO datetime string to datetime object

    Args:
        iso_string: ISO format datetime string

    Returns:
        datetime object
    """
    try:
        # Handle different ISO formats
        if iso_string.endswith('Z'):
            iso_string = iso_string[:-1] + '+00:00'
        elif '+' not in iso_string and iso_string.count(':') == 2:
            # Add timezone if missing
            iso_string += '+00:00'

        return datetime.fromisoformat(iso_string)
    except ValueError as e:
        logger.warning(f"Failed to parse datetime string '{iso_string}': {e}")
        return datetime.now(timezone.utc)


def format_datetime_for_api(dt: datetime) -> str:
    """
    Format datetime for API responses

    Args:
        dt: datetime object

    Returns:
        ISO format string
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate latitude and longitude coordinates

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        True if valid, False otherwise
    """
    return (-90.0 <= lat <= 90.0) and (-180.0 <= lon <= 180.0)


def calculate_pagination_info(total_items: int, page: int, page_size: int) -> Dict[str, Any]:
    """
    Calculate pagination information

    Args:
        total_items: Total number of items
        page: Current page number (1-based)
        page_size: Items per page

    Returns:
        Dictionary with pagination info
    """
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "offset": (page - 1) * page_size
    }


def sanitize_query_string(query: str, max_length: int = 200) -> str:
    """
    Sanitize user query string for safety

    Args:
        query: User input query
        max_length: Maximum allowed length

    Returns:
        Sanitized query string
    """
    if not query:
        return ""

    # Trim to max length
    query = query[:max_length]

    # Remove potentially harmful characters
    query = re.sub(r'[<>"\']', '', query)

    # Normalize whitespace
    query = re.sub(r'\s+', ' ', query).strip()

    return query


def create_error_response(error_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create standardized error response

    Args:
        error_type: Type of error
        message: Error message
        details: Additional error details

    Returns:
        Error response dictionary
    """
    return {
        "error": error_type,
        "message": message,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat()
    }


def create_success_response(message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create standardized success response

    Args:
        message: Success message
        data: Response data

    Returns:
        Success response dictionary
    """
    return {
        "success": True,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }


async def retry_async_operation(operation, max_retries: int = 3, delay: float = 1.0,
                                backoff_factor: float = 2.0):
    """
    Retry an async operation with exponential backoff

    Args:
        operation: Async function to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by for each retry

    Returns:
        Result of the operation

    Raises:
        The last exception if all retries fail
    """
    last_exception = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")

    if last_exception:
        raise last_exception


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with suffix

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def extract_domain_from_url(url: str) -> str:
    """
    Extract domain from URL

    Args:
        url: URL string

    Returns:
        Domain name
    """
    try:
        # Simple regex to extract domain
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        return match.group(1) if match else url
    except Exception:
        return url


def is_valid_uuid(uuid_string: str) -> bool:
    """
    Check if string is a valid UUID

    Args:
        uuid_string: String to validate

    Returns:
        True if valid UUID, False otherwise
    """
    import uuid
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False