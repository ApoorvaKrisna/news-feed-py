import asyncio
import random
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.services.database import DatabaseService
from app.models.news_models import UserEvent, UserEventDocument, TrendingArticle, EnrichedNewsArticle
from app.config import settings


class TrendingService:
    """Service for managing trending news and user interactions"""

    def __init__(self, db_service: DatabaseService):
        self.db = db_service
        self.event_types = ["view", "click", "share", "like", "comment"]
        self.event_weights = {
            "view": 1.0,
            "click": 2.0,
            "share": 3.0,
            "like": 1.5,
            "comment": 2.5
        }

    async def get_trending_articles(self, user_lat: float, user_lon: float,
                                    radius: float = 10.0, limit: int = 10,
                                    hours_back: int = 24) -> List[TrendingArticle]:
        """
        Get trending articles based on user interactions
        """
        try:
            # Get trending data from database
            trending_data = await self.db.get_trending_articles(
                user_lat, user_lon, radius, hours_back, limit
            )

            trending_articles = []
            for data in trending_data:
                # Convert article data to EnrichedNewsArticle
                article_data = data["article"]
                enriched_article = EnrichedNewsArticle(**article_data)

                # Create TrendingArticle
                trending_article = TrendingArticle(
                    article=enriched_article,
                    trending_score=data["trending_score"],
                    interaction_count=data["total_interactions"],
                    unique_users=data["unique_users"],
                    recent_interactions=data["recent_interactions"]
                )

                trending_articles.append(trending_article)

            logger.info(f"Retrieved {len(trending_articles)} trending articles for location ({user_lat}, {user_lon})")
            return trending_articles

        except Exception as e:
            logger.error(f"Error getting trending articles: {e}")
            # Return empty list on error
            return []

    async def simulate_user_interactions(self, num_events: int = 100,
                                         location_radius: float = 50.0) -> int:
        """
        Simulate user interaction events for testing trending functionality
        """
        try:
            # Get some random articles to simulate interactions with
            articles = await self.db.get_random_articles(min(20, num_events // 3))

            if not articles:
                logger.warning("No articles found to simulate interactions")
                return 0

            events_created = 0
            base_time = datetime.utcnow()

            # Generate random users
            user_ids = [f"user_{uuid.uuid4().hex[:8]}" for _ in range(min(10, num_events // 5))]

            for i in range(num_events):
                try:
                    # Select random article and user
                    article = random.choice(articles)
                    user_id = random.choice(user_ids)

                    # Generate random event type (weighted towards views)
                    event_type = random.choices(
                        self.event_types,
                        weights=[4, 3, 1, 2, 1],  # More views, fewer shares
                        k=1
                    )[0]

                    # Generate location near the article with some randomness
                    lat_offset = random.uniform(-location_radius / 111, location_radius / 111)  # ~1 degree = 111km
                    lon_offset = random.uniform(-location_radius / 111, location_radius / 111)

                    user_lat = article.latitude + lat_offset
                    user_lon = article.longitude + lon_offset

                    # Ensure coordinates are within valid range
                    user_lat = max(-90, min(90, user_lat))
                    user_lon = max(-180, min(180, user_lon))

                    # Generate timestamp (recent events are more likely)
                    hours_back = random.choices(
                        range(1, 25),
                        weights=[10, 8, 6, 4, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        k=1
                    )[0]

                    event_time = base_time - timedelta(hours=hours_back)

                    # Create user event
                    event = UserEventDocument(
                        user_id=user_id,
                        article_id=article.id,
                        event_type=event_type,
                        timestamp=event_time,
                        user_latitude=user_lat,
                        user_longitude=user_lon,
                        session_id=f"session_{uuid.uuid4().hex[:8]}"
                    )

                    # Insert event into database
                    await self.db.insert_user_event(event)
                    events_created += 1

                    # Add small delay to avoid overwhelming the database
                    if i % 10 == 0:
                        await asyncio.sleep(0.1)

                except Exception as e:
                    logger.warning(f"Failed to create simulated event {i}: {e}")
                    continue

            logger.info(f"Successfully created {events_created} simulated user interaction events")
            return events_created

        except Exception as e:
            logger.error(f"Error simulating user interactions: {e}")
            return 0

    async def record_user_interaction(self, user_id: str, article_id: str,
                                      event_type: str, user_lat: float, user_lon: float,
                                      session_id: Optional[str] = None) -> bool:
        """
        Record a real user interaction event
        """
        try:
            if event_type not in self.event_types:
                logger.warning(f"Invalid event type: {event_type}")
                return False

            event = UserEventDocument(
                user_id=user_id,
                article_id=article_id,
                event_type=event_type,
                timestamp=datetime.utcnow(),
                user_latitude=user_lat,
                user_longitude=user_lon,
                session_id=session_id or f"session_{uuid.uuid4().hex[:8]}"
            )

            await self.db.insert_user_event(event)
            logger.info(f"Recorded {event_type} event for user {user_id} on article {article_id}")
            return True

        except Exception as e:
            logger.error(f"Error recording user interaction: {e}")
            return False

    async def get_user_activity_stats(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get statistics about user activity in the specified time period
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

            # Use aggregation pipeline to get stats
            pipeline = [
                {"$match": {"timestamp": {"$gte": cutoff_time}}},
                {
                    "$group": {
                        "_id": None,
                        "total_events": {"$sum": 1},
                        "unique_users": {"$addToSet": "$user_id"},
                        "unique_articles": {"$addToSet": "$article_id"},
                        "event_types": {"$push": "$event_type"}
                    }
                },
                {
                    "$project": {
                        "total_events": 1,
                        "unique_users_count": {"$size": "$unique_users"},
                        "unique_articles_count": {"$size": "$unique_articles"},
                        "event_type_counts": {
                            "$arrayToObject": {
                                "$map": {
                                    "input": {"$setUnion": ["$event_types", []]},
                                    "as": "event_type",
                                    "in": {
                                        "k": "$event_type",
                                        "v": {
                                            "$size": {
                                                "$filter": {
                                                    "input": "$event_types",
                                                    "cond": {"$eq": ["$this", "$event_type"]}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            ]

            result = await self.db.events_collection.aggregate(pipeline).to_list(1)

            if result:
                stats = result[0]
                return {
                    "total_events": stats.get("total_events", 0),
                    "unique_users": stats.get("unique_users_count", 0),
                    "unique_articles": stats.get("unique_articles_count", 0),
                    "event_breakdown": stats.get("event_type_counts", {}),
                    "hours_analyzed": hours_back,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "total_events": 0,
                    "unique_users": 0,
                    "unique_articles": 0,
                    "event_breakdown": {},
                    "hours_analyzed": hours_back,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Error getting user activity stats: {e}")
            return {
                "error": str(e),
                "hours_analyzed": hours_back,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

    async def get_trending_by_location_clusters(self, lat: float, lon: float,
                                                cluster_size: float = 5.0,
                                                limit: int = 10) -> List[TrendingArticle]:
        """
        Get trending articles using location clustering for better caching
        """
        try:
            # Simple grid-based clustering
            cluster_lat = round(lat / cluster_size) * cluster_size
            cluster_lon = round(lon / cluster_size) * cluster_size

            # Use a larger radius for clustered search
            radius = cluster_size * 1.5

            return await self.get_trending_articles(
                cluster_lat, cluster_lon, radius, limit
            )

        except Exception as e:
            logger.error(f"Error getting clustered trending articles: {e}")
            return []

    def calculate_trending_score(self, interactions: List[Dict[str, Any]],
                                 article_age_hours: float,
                                 distance_km: float = 0) -> float:
        """
        Calculate trending score based on interactions, recency, and proximity
        """
        try:
            if not interactions:
                return 0.0

            # Base score from weighted interactions
            interaction_score = 0
            unique_users = set()

            for interaction in interactions:
                event_type = interaction.get("event_type", "view")
                user_id = interaction.get("user_id", "")

                # Weight by event type
                weight = self.event_weights.get(event_type, 1.0)
                interaction_score += weight
                unique_users.add(user_id)

            # Bonus for unique users (viral factor)
            unique_user_bonus = len(unique_users) * 1.5

            # Time decay (newer articles get higher scores)
            time_factor = max(0.1, 1.0 - (article_age_hours / 168))  # Decay over 1 week

            # Distance decay (closer articles get higher scores)
            distance_factor = max(0.1, 1.0 - (distance_km / 100))  # Decay over 100km

            # Final trending score
            trending_score = (interaction_score + unique_user_bonus) * time_factor * distance_factor

            return trending_score

        except Exception as e:
            logger.error(f"Error calculating trending score: {e}")
            return 0.0

    async def cleanup_old_events(self, days_to_keep: int = 7) -> int:
        """
        Clean up old user interaction events to manage database size
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            result = await self.db.events_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })

            deleted_count = result.deleted_count
            logger.info(f"Cleaned up {deleted_count} old user interaction events (older than {days_to_keep} days)")

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old events: {e}")
            return 0

    async def get_popular_articles_by_region(self, min_lat: float, max_lat: float,
                                             min_lon: float, max_lon: float,
                                             hours_back: int = 24,
                                             limit: int = 10) -> List[TrendingArticle]:
        """
        Get popular articles within a geographic bounding box
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

            pipeline = [
                # Match events within time and geographic bounds
                {
                    "$match": {
                        "timestamp": {"$gte": cutoff_time},
                        "user_latitude": {"$gte": min_lat, "$lte": max_lat},
                        "user_longitude": {"$gte": min_lon, "$lte": max_lon}
                    }
                },
                # Group by article and calculate metrics
                {
                    "$group": {
                        "_id": "$article_id",
                        "total_interactions": {"$sum": 1},
                        "unique_users": {"$addToSet": "$user_id"},
                        "event_types": {"$push": "$event_type"},
                        "avg_lat": {"$avg": "$user_latitude"},
                        "avg_lon": {"$avg": "$user_longitude"}
                    }
                },
                # Calculate trending score
                {
                    "$addFields": {
                        "unique_user_count": {"$size": "$unique_users"},
                        "trending_score": {
                            "$multiply": [
                                {"$ln": {"$add": ["$total_interactions", 1]}},
                                {"$ln": {"$add": [{"$size": "$unique_users"}, 1]}}
                            ]
                        }
                    }
                },
                # Sort and limit
                {"$sort": {"trending_score": -1}},
                {"$limit": limit},
                # Join with articles
                {
                    "$lookup": {
                        "from": "articles",
                        "localField": "_id",
                        "foreignField": "id",
                        "as": "article"
                    }
                },
                {"$unwind": "$article"}
            ]

            results = await self.db.events_collection.aggregate(pipeline).to_list(limit)

            trending_articles = []
            for result in results:
                article_data = result["article"]
                enriched_article = EnrichedNewsArticle(**article_data)

                trending_article = TrendingArticle(
                    article=enriched_article,
                    trending_score=result["trending_score"],
                    interaction_count=result["total_interactions"],
                    unique_users=result["unique_user_count"],
                    recent_interactions=result["total_interactions"]  # All are recent in this query
                )

                trending_articles.append(trending_article)

            return trending_articles

        except Exception as e:
            logger.error(f"Error getting popular articles by region: {e}")
            return []