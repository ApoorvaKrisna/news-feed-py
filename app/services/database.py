import motor.motor_asyncio
from pymongo import IndexModel, ASCENDING, TEXT, GEOSPHERE
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math
from loguru import logger

from app.config import settings
from app.models.news_models import NewsArticle, NewsArticleDocument, UserEventDocument


class DatabaseService:
    """Database service for MongoDB operations"""

    def __init__(self):
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.database: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self.articles_collection: Optional[motor.motor_asyncio.AsyncIOMotorCollection] = None
        self.events_collection: Optional[motor.motor_asyncio.AsyncIOMotorCollection] = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)
            self.database = self.client[settings.database_name]
            self.articles_collection = self.database["articles"]  # Updated collection name
            self.events_collection = self.database["user_events"]

            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")

            # Create indexes
            await self.create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def ping(self):
        """Ping database to check connection"""
        if self.client:
            await self.client.admin.command('ping')
        else:
            raise Exception("Database not connected")

    async def create_indexes(self):
        """Create necessary indexes for optimal performance"""
        try:
            # Articles collection indexes
            indexes = [
                # Basic search indexes
                IndexModel([("category", ASCENDING)], name="category_idx"),
                IndexModel([("source_name", ASCENDING)], name="source_idx"),
                IndexModel([("relevance_score", -1)], name="relevance_score_idx"),
                IndexModel([("publication_date", -1)], name="publication_date_idx"),
                IndexModel([("id", ASCENDING)], name="id_idx", unique=True),

                # Location indexes for nearby search
                IndexModel([("latitude", ASCENDING), ("longitude", ASCENDING)], name="location_idx"),

                # Text search index
                IndexModel([("title", TEXT), ("description", TEXT)], name="text_search_idx"),

                # Compound indexes for common query patterns (PERFORMANCE OPTIMIZATION)
                IndexModel([("category", ASCENDING), ("publication_date", -1)], name="category_date_idx"),
                IndexModel([("source_name", ASCENDING), ("publication_date", -1)], name="source_date_idx"),
                IndexModel([("relevance_score", -1), ("publication_date", -1)], name="score_date_idx"),

                # Location-based compound indexes for geospatial queries
                IndexModel([("latitude", ASCENDING), ("longitude", ASCENDING), ("relevance_score", -1)],
                           name="location_score_idx"),

                # Trending analysis indexes
                IndexModel([("category", ASCENDING), ("relevance_score", -1)], name="category_score_idx"),
            ]

            await self.articles_collection.create_indexes(indexes)

            # User events collection indexes (for trending functionality)
            event_indexes = [
                IndexModel([("article_id", ASCENDING)], name="article_id_idx"),
                IndexModel([("user_id", ASCENDING)], name="user_id_idx"),
                IndexModel([("timestamp", -1)], name="timestamp_idx"),
                IndexModel([("event_type", ASCENDING)], name="event_type_idx"),

                # Compound indexes for trending analysis (PERFORMANCE OPTIMIZATION)
                IndexModel([("timestamp", -1), ("event_type", ASCENDING)], name="time_event_idx"),
                IndexModel([("article_id", ASCENDING), ("timestamp", -1)], name="article_time_idx"),
                IndexModel([("user_latitude", ASCENDING), ("user_longitude", ASCENDING), ("timestamp", -1)],
                           name="location_time_idx"),
            ]

            await self.events_collection.create_indexes(event_indexes)
            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.warning(f"Some indexes may already exist: {e}")

    # --- News Articles Queries ---

    async def get_articles_by_category(self, category: str, limit: int = 5, offset: int = 0) -> Tuple[
        List[NewsArticle], int]:
        """Get articles by category"""
        pipeline = [
            {"$match": {"category": {"$in": [category]}}},
            {"$sort": {"publication_date": -1}},
            {"$facet": {
                "articles": [{"$skip": offset}, {"$limit": limit}],
                "total": [{"$count": "count"}]
            }}
        ]

        result = await self.articles_collection.aggregate(pipeline).to_list(1)
        articles_data = result[0]["articles"] if result else []
        total_count = result[0]["total"][0]["count"] if result and result[0]["total"] else 0

        articles = [NewsArticle(**doc) for doc in articles_data]
        return articles, total_count

    async def get_articles_by_score(self, min_score: float, limit: int = 5, offset: int = 0) -> Tuple[
        List[NewsArticle], int]:
        """Get articles by minimum relevance score"""
        pipeline = [
            {"$match": {"relevance_score": {"$gte": min_score}}},
            {"$sort": {"relevance_score": -1}},
            {"$facet": {
                "articles": [{"$skip": offset}, {"$limit": limit}],
                "total": [{"$count": "count"}]
            }}
        ]

        result = await self.articles_collection.aggregate(pipeline).to_list(1)
        articles_data = result[0]["articles"] if result else []
        total_count = result[0]["total"][0]["count"] if result and result[0]["total"] else 0

        articles = [NewsArticle(**doc) for doc in articles_data]
        return articles, total_count

    async def search_articles(self, query: str, limit: int = 5, offset: int = 0) -> Tuple[List[NewsArticle], int]:
        """Search articles by text in title and description"""
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"title": {"$regex": query, "$options": "i"}},
                        {"description": {"$regex": query, "$options": "i"}}
                    ]
                }
            },
            {
                "$addFields": {
                    "text_match_score": {
                        "$add": [
                            {"$cond": [{"$regexMatch": {"input": "$title", "regex": query, "options": "i"}}, 0.7, 0]},
                            {"$cond": [{"$regexMatch": {"input": "$description", "regex": query, "options": "i"}}, 0.3,
                                       0]}
                        ]
                    }
                }
            },
            {"$sort": {"text_match_score": -1, "relevance_score": -1}},
            {"$facet": {
                "articles": [{"$skip": offset}, {"$limit": limit}],
                "total": [{"$count": "count"}]
            }}
        ]

        result = await self.articles_collection.aggregate(pipeline).to_list(1)
        articles_data = result[0]["articles"] if result else []
        total_count = result[0]["total"][0]["count"] if result and result[0]["total"] else 0

        articles = [NewsArticle(**doc) for doc in articles_data]
        return articles, total_count

    async def get_articles_by_source(self, source: str, limit: int = 5, offset: int = 0) -> Tuple[
        List[NewsArticle], int]:
        """Get articles by source"""
        pipeline = [
            {"$match": {"source_name": {"$regex": source, "$options": "i"}}},
            {"$sort": {"publication_date": -1}},
            {"$facet": {
                "articles": [{"$skip": offset}, {"$limit": limit}],
                "total": [{"$count": "count"}]
            }}
        ]

        result = await self.articles_collection.aggregate(pipeline).to_list(1)
        articles_data = result[0]["articles"] if result else []
        total_count = result[0]["total"][0]["count"] if result and result[0]["total"] else 0

        articles = [NewsArticle(**doc) for doc in articles_data]
        return articles, total_count

    async def get_nearby_articles(self, lat: float, lon: float, radius_km: float, limit: int = 5, offset: int = 0) -> \
    Tuple[List[NewsArticle], int]:
        """Get articles within radius using Haversine distance calculation"""

        # Use aggregation pipeline with distance calculation
        pipeline = [
            {
                "$addFields": {
                    "distance_km": {
                        "$multiply": [
                            6371,  # Earth's radius in km
                            {
                                "$acos": {
                                    "$add": [
                                        {
                                            "$multiply": [
                                                {"$sin": {"$multiply": [{"$degreesToRadians": lat}, 1]}},
                                                {"$sin": {"$multiply": [{"$degreesToRadians": "$latitude"}, 1]}}
                                            ]
                                        },
                                        {
                                            "$multiply": [
                                                {"$cos": {"$multiply": [{"$degreesToRadians": lat}, 1]}},
                                                {"$cos": {"$multiply": [{"$degreesToRadians": "$latitude"}, 1]}},
                                                {"$cos": {
                                                    "$subtract": [
                                                        {"$multiply": [{"$degreesToRadians": "$longitude"}, 1]},
                                                        {"$multiply": [{"$degreesToRadians": lon}, 1]}
                                                    ]
                                                }}
                                            ]
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            },
            {
                "$match": {
                    "distance_km": {"$lte": radius_km}
                }
            },
            {"$sort": {"distance_km": 1}},
            {
                "$facet": {
                    "articles": [{"$skip": offset}, {"$limit": limit}],
                    "total": [{"$count": "count"}]
                }
            }
        ]

        result = await self.articles_collection.aggregate(pipeline).to_list(1)
        articles_data = result[0]["articles"] if result else []
        total_count = result[0]["total"][0]["count"] if result and result[0]["total"] else 0

        articles = [NewsArticle(**doc) for doc in articles_data]
        return articles, total_count

    # --- User Events for Trending ---

    async def insert_user_event(self, event: UserEventDocument):
        """Insert a user interaction event"""
        await self.events_collection.insert_one(event.dict(by_alias=True))

    async def get_trending_articles(self, user_lat: float, user_lon: float, radius_km: float,
                                    hours_back: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending articles based on user interactions"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        radius_meters = radius_km * 1000

        pipeline = [
            # Match recent events within radius
            {
                "$geoNear": {
                    "near": {"type": "Point", "coordinates": [user_lon, user_lat]},
                    "distanceField": "user_distance_meters",
                    "maxDistance": radius_meters,
                    "spherical": True,
                    "query": {"timestamp": {"$gte": cutoff_time}}
                }
            },
            # Group by article and calculate trending metrics
            {
                "$group": {
                    "_id": "$article_id",
                    "total_interactions": {"$sum": 1},
                    "unique_users": {"$addToSet": "$user_id"},
                    "recent_interactions": {"$sum": 1},
                    "avg_distance": {"$avg": "$user_distance_meters"},
                    "interaction_types": {"$push": "$event_type"}
                }
            },
            # Calculate trending score
            {
                "$addFields": {
                    "unique_user_count": {"$size": "$unique_users"},
                    "trending_score": {
                        "$multiply": [
                            {"$ln": {"$add": ["$total_interactions", 1]}},
                            {"$ln": {"$add": ["$unique_user_count", 1]}},
                            {"$divide": [1, {"$add": [{"$divide": ["$avg_distance", 1000]}, 1]}]}
                        ]
                    }
                }
            },
            # Sort by trending score
            {"$sort": {"trending_score": -1}},
            {"$limit": limit},
            # Join with articles collection
            {
                "$lookup": {
                    "from": "articles",
                    "localField": "_id",
                    "foreignField": "id",
                    "as": "article"
                }
            },
            {"$unwind": "$article"},
            # Project final result
            {
                "$project": {
                    "article": "$article",
                    "trending_score": 1,
                    "total_interactions": 1,
                    "unique_users": "$unique_user_count",
                    "recent_interactions": 1
                }
            }
        ]

        return await self.events_collection.aggregate(pipeline).to_list(limit)

    # --- Utility Methods ---

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    async def get_article_by_id(self, article_id: str) -> Optional[NewsArticle]:
        """Get a specific article by ID"""
        doc = await self.articles_collection.find_one({"id": article_id})
        return NewsArticle(**doc) if doc else None

    async def get_random_articles(self, limit: int = 5) -> List[NewsArticle]:
        """Get random articles for testing"""
        pipeline = [{"$sample": {"size": limit}}]
        docs = await self.articles_collection.aggregate(pipeline).to_list(limit)
        return [NewsArticle(**doc) for doc in docs]

    async def get_all_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = await self.articles_collection.distinct("category")
        return sorted(categories)

    async def get_all_sources(self) -> List[str]:
        """Get all unique sources"""
        sources = await self.articles_collection.distinct("source_name")
        return sorted(sources)