from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
from loguru import logger

from app.services.database import DatabaseService
from app.services.llm_service import LLMService
from app.models.news_models import NewsArticle, EnrichedNewsArticle, NewsArticleResponse
from app.models.api_models import QueryInfo, PaginationInfo
from app.models.llm_models import LLMAnalysis, QueryProcessingResponse


class NewsService:
    """Business logic service for news operations"""

    def __init__(self, db_service: DatabaseService, llm_service: LLMService):
        self.db = db_service
        self.llm = llm_service

    async def intelligent_query(self, query: str, user_lat: Optional[float] = None,
                                user_lon: Optional[float] = None, limit: int = 5,
                                include_summary: bool = True) -> NewsArticleResponse:
        """
        Process an intelligent query using LLM analysis
        """
        start_time = datetime.utcnow()

        try:
            # Prepare user location
            user_location = None
            if user_lat is not None and user_lon is not None:
                user_location = {"lat": user_lat, "lon": user_lon}

            # Process query with LLM
            processing_response = await self.llm.process_query_intelligently(query, user_location)
            analysis = processing_response.analysis
            endpoint = processing_response.suggested_endpoint
            parameters = processing_response.query_parameters

            # Execute the determined search strategy
            articles, total_count = await self._execute_search_strategy(
                endpoint, parameters, limit
            )

            # Enrich articles with LLM summaries if requested
            enriched_articles = await self._enrich_articles(
                articles, include_summary, user_location
            )

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Create query info
            query_info = QueryInfo(
                original_query=query,
                processed_query=" ".join(analysis.keywords) if analysis.keywords else query,
                intent=analysis.intent.value,
                entities=[entity.text for entity in analysis.entities],
                location_used=user_location,
                processing_time_ms=processing_time
            )

            return NewsArticleResponse(
                articles=enriched_articles,
                total_count=total_count,
                page=1,
                page_size=limit,
                query_info=query_info.dict()
            )

        except Exception as e:
            logger.error(f"Error in intelligent query processing: {e}")
            raise

    async def get_articles_by_category(self, category: str, limit: int = 5,
                                       offset: int = 0) -> NewsArticleResponse:
        """Get articles by category with sorting by publication date"""
        try:
            articles, total_count = await self.db.get_articles_by_category(category, limit, offset)
            enriched_articles = [self._convert_to_enriched(article) for article in articles]

            return NewsArticleResponse(
                articles=enriched_articles,
                total_count=total_count,
                page=(offset // limit) + 1,
                page_size=limit
            )
        except Exception as e:
            logger.error(f"Error getting articles by category '{category}': {e}")
            raise

    async def get_articles_by_score(self, min_score: float, limit: int = 5,
                                    offset: int = 0) -> NewsArticleResponse:
        """Get articles by minimum relevance score"""
        try:
            articles, total_count = await self.db.get_articles_by_score(min_score, limit, offset)
            enriched_articles = [self._convert_to_enriched(article) for article in articles]

            return NewsArticleResponse(
                articles=enriched_articles,
                total_count=total_count,
                page=(offset // limit) + 1,
                page_size=limit
            )
        except Exception as e:
            logger.error(f"Error getting articles by score >= {min_score}: {e}")
            raise

    async def search_articles(self, query: str, limit: int = 5, offset: int = 0,
                              include_summaries: bool = False) -> NewsArticleResponse:
        """Search articles by text with optional LLM summaries"""
        try:
            articles, total_count = await self.db.search_articles(query, limit, offset)

            if include_summaries:
                enriched_articles = await self._enrich_articles(articles, True)
            else:
                enriched_articles = [self._convert_to_enriched(article) for article in articles]

            return NewsArticleResponse(
                articles=enriched_articles,
                total_count=total_count,
                page=(offset // limit) + 1,
                page_size=limit
            )
        except Exception as e:
            logger.error(f"Error searching articles with query '{query}': {e}")
            raise

    async def get_articles_by_source(self, source: str, limit: int = 5,
                                     offset: int = 0) -> NewsArticleResponse:
        """Get articles by source"""
        try:
            articles, total_count = await self.db.get_articles_by_source(source, limit, offset)
            enriched_articles = [self._convert_to_enriched(article) for article in articles]

            return NewsArticleResponse(
                articles=enriched_articles,
                total_count=total_count,
                page=(offset // limit) + 1,
                page_size=limit
            )
        except Exception as e:
            logger.error(f"Error getting articles by source '{source}': {e}")
            raise

    async def get_nearby_articles(self, lat: float, lon: float, radius: float = 10.0,
                                  limit: int = 5, offset: int = 0) -> NewsArticleResponse:
        """Get articles near a location"""
        try:
            articles, total_count = await self.db.get_nearby_articles(lat, lon, radius, limit, offset)

            # Add distance information to articles
            enriched_articles = []
            for article in articles:
                enriched_article = self._convert_to_enriched(article)
                # Calculate distance if not already provided
                if not hasattr(enriched_article, 'distance_km') or enriched_article.distance_km is None:
                    distance = self.db.calculate_distance(lat, lon, article.latitude, article.longitude)
                    enriched_article.distance_km = distance
                enriched_articles.append(enriched_article)

            return NewsArticleResponse(
                articles=enriched_articles,
                total_count=total_count,
                page=(offset // limit) + 1,
                page_size=limit
            )
        except Exception as e:
            logger.error(f"Error getting nearby articles: {e}")
            raise

    async def _execute_search_strategy(self, endpoint: str, parameters: Dict[str, Any],
                                       limit: int) -> Tuple[List[NewsArticle], int]:
        """Execute the determined search strategy"""
        # Ensure limit is in parameters
        parameters["limit"] = limit

        if endpoint == "category":
            return await self.db.get_articles_by_category(
                parameters["category"],
                parameters.get("limit", 5),
                parameters.get("offset", 0)
            )

        elif endpoint == "source":
            return await self.db.get_articles_by_source(
                parameters["source"],
                parameters.get("limit", 5),
                parameters.get("offset", 0)
            )

        elif endpoint == "nearby":
            return await self.db.get_nearby_articles(
                parameters["lat"],
                parameters["lon"],
                parameters.get("radius", 10.0),
                parameters.get("limit", 5),
                parameters.get("offset", 0)
            )

        elif endpoint == "score":
            return await self.db.get_articles_by_score(
                parameters.get("min_score", 0.7),
                parameters.get("limit", 5),
                parameters.get("offset", 0)
            )

        else:  # Default to search
            return await self.db.search_articles(
                parameters.get("query", ""),
                parameters.get("limit", 5),
                parameters.get("offset", 0)
            )

    async def _enrich_articles(self, articles: List[NewsArticle],
                               include_summary: bool = True,
                               user_location: Optional[Dict[str, float]] = None) -> List[EnrichedNewsArticle]:
        """Enrich articles with LLM summaries and additional information"""
        if not articles:
            return []

        enriched_articles = []

        # Generate summaries if requested
        if include_summary:
            summaries = await self.llm.batch_generate_summaries(articles)
        else:
            summaries = [None] * len(articles)

        for article, summary in zip(articles, summaries):
            enriched_article = self._convert_to_enriched(article)

            # Add LLM summary
            if summary:
                enriched_article.llm_summary = summary.summary

            # Add distance if user location provided
            if user_location and 'lat' in user_location and 'lon' in user_location:
                distance = self.db.calculate_distance(
                    user_location['lat'], user_location['lon'],
                    article.latitude, article.longitude
                )
                enriched_article.distance_km = distance

            enriched_articles.append(enriched_article)

        return enriched_articles

    def _convert_to_enriched(self, article: NewsArticle) -> EnrichedNewsArticle:
        """Convert NewsArticle to EnrichedNewsArticle"""
        return EnrichedNewsArticle(**article.dict())

    async def get_available_categories(self) -> List[str]:
        """Get all available categories"""
        return await self.db.get_all_categories()

    async def get_available_sources(self) -> List[str]:
        """Get all available sources"""
        return await self.db.get_all_sources()

    async def get_random_articles(self, limit: int = 5) -> List[EnrichedNewsArticle]:
        """Get random articles for testing"""
        articles = await self.db.get_random_articles(limit)
        return [self._convert_to_enriched(article) for article in articles]

    async def get_article_by_id(self, article_id: str) -> Optional[EnrichedNewsArticle]:
        """Get a specific article by ID"""
        article = await self.db.get_article_by_id(article_id)
        if article:
            return self._convert_to_enriched(article)
        return None