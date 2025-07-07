import openai
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from app.config import settings
from app.models.llm_models import (
    LLMAnalysis, LLMIntent, ExtractedEntity, SummaryResponse,
    LLMError, QueryProcessingResponse, LLMPrompts
)
from app.models.news_models import NewsArticle


class LLMService:
    """Service for OpenAI LLM interactions"""

    def __init__(self):
        # Initialize OpenAI client
        openai.api_key = settings.openai_api_key
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature

        # Available categories from your data
        self.available_categories = [
            "national", "sports", "General", "world", "business", "entertainment",
            "politics", "IPL*2025", "technology", "Health___Fitness", "startup",
            "IPL", "science", "FINANCE", "cricket", "hatke", "education",
            "Russia-Ukraine*Conflict", "EXPLAINERS"
        ]

        # Available sources from your data
        self.available_sources = [
            "Hindustan Times", "Free Press Journal", "News Karnataka", "News18",
            "ET Now", "The Indian Express", "Moneycontrol", "Youtube", "Reuters",
            "Times Now", "PTI", "ANI", "Sports Tiger", "Investment Guru India", "Cricfit"
        ]

    async def analyze_query(self, query: str, user_location: Optional[Dict[str, float]] = None) -> LLMAnalysis:
        """
        Analyze user query to extract entities, intent, and relevant information
        """
        try:
            location_str = "not provided"
            if user_location and 'lat' in user_location and 'lon' in user_location:
                location_str = f"lat: {user_location['lat']}, lon: {user_location['lon']}"

            prompt = LLMPrompts.ENTITY_EXTRACTION.format(
                query=query,
                categories=", ".join(self.available_categories),
                sources=", ".join(self.available_sources)
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "You are an expert at analyzing news queries and extracting relevant information. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                analysis_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                analysis_data = self._fallback_query_analysis(query, user_location)

            # Validate and create entities
            entities = []
            for entity_data in analysis_data.get("entities", []):
                try:
                    entities.append(ExtractedEntity(**entity_data))
                except Exception as e:
                    logger.warning(f"Invalid entity data: {entity_data}, error: {e}")

            # Create LLM analysis object
            analysis = LLMAnalysis(
                original_query=query,
                intent=LLMIntent(analysis_data.get("intent", "general")),
                entities=entities,
                keywords=analysis_data.get("keywords", []),
                location_mentioned=analysis_data.get("location_mentioned"),
                category_mentioned=analysis_data.get("category_mentioned"),
                source_mentioned=analysis_data.get("source_mentioned"),
                confidence=analysis_data.get("confidence", 0.7),
                reasoning=analysis_data.get("reasoning", "Analysis completed")
            )

            logger.info(f"Successfully analyzed query: '{query}' -> Intent: {analysis.intent}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing query '{query}': {e}")
            # Return fallback analysis
            return self._fallback_query_analysis(query, user_location)

    async def generate_summary(self, article: NewsArticle, max_length: int = 150) -> SummaryResponse:
        """
        Generate LLM summary for a news article
        """
        try:
            prompt = LLMPrompts.SUMMARY_GENERATION.format(
                title=article.title,
                description=article.description,
                max_length=max_length
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "You are an expert news summarizer. Create concise, informative summaries and respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=min(self.max_tokens, max_length + 100),
                temperature=0.3,  # Lower temperature for more consistent summaries
                timeout=10.0  # Add timeout to prevent hanging
            )

            content = response.choices[0].message.content.strip()

            try:
                summary_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback summary
                summary_data = {
                    "summary": article.description[:max_length] + "..." if len(
                        article.description) > max_length else article.description,
                    "key_points": [article.title],
                    "sentiment": "neutral",
                    "topics": ["news"]
                }

            summary = SummaryResponse(
                summary=summary_data.get("summary", "")[:max_length],
                key_points=summary_data.get("key_points", [])[:3],  # Limit to 3 key points
                sentiment=summary_data.get("sentiment", "neutral"),
                topics=summary_data.get("topics", [])[:5]  # Limit to 5 topics
            )

            return summary

        except Exception as e:
            logger.error(f"Error generating summary for article {article.id}: {e}")
            # Return fallback summary
            return SummaryResponse(
                summary=article.description[:max_length] + "..." if len(
                    article.description) > max_length else article.description,
                key_points=[article.title],
                sentiment="neutral",
                topics=["news"]
            )

    async def batch_generate_summaries(self, articles: List[NewsArticle], max_length: int = 150) -> List[
        SummaryResponse]:
        """
        Generate summaries for multiple articles concurrently
        """
        if not articles:
            return []

        # Limit concurrent requests to avoid rate limiting
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

        async def generate_with_semaphore(article):
            async with semaphore:
                return await self.generate_summary(article, max_length)

        tasks = [generate_with_semaphore(article) for article in articles]
        summaries = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions in the results
        result_summaries = []
        for i, summary in enumerate(summaries):
            if isinstance(summary, Exception):
                logger.error(f"Error generating summary for article {articles[i].id}: {summary}")
                # Create fallback summary
                result_summaries.append(SummaryResponse(
                    summary=articles[i].description[:max_length] + "..." if len(
                        articles[i].description) > max_length else articles[i].description,
                    key_points=[articles[i].title],
                    sentiment="neutral",
                    topics=["news"]
                ))
            else:
                result_summaries.append(summary)

        return result_summaries

    async def classify_intent(self, query: str, user_location: Optional[Dict[str, float]] = None) -> Tuple[
        LLMIntent, float]:
        """
        Classify the intent of a user query
        """
        try:
            location_str = "not provided"
            if user_location:
                location_str = f"lat: {user_location.get('lat', 'unknown')}, lon: {user_location.get('lon', 'unknown')}"

            prompt = LLMPrompts.INTENT_CLASSIFICATION.format(
                query=query,
                user_location=location_str
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system",
                     "content": "You are an expert at classifying search intents for news queries. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.2
            )

            content = response.choices[0].message.content.strip()

            try:
                intent_data = json.loads(content)
                intent = LLMIntent(intent_data.get("intent", "general"))
                confidence = intent_data.get("confidence", 0.7)
                return intent, confidence
            except (json.JSONDecodeError, ValueError):
                return LLMIntent.GENERAL, 0.5

        except Exception as e:
            logger.error(f"Error classifying intent for query '{query}': {e}")
            return LLMIntent.GENERAL, 0.5

    def _fallback_query_analysis(self, query: str, user_location: Optional[Dict[str, float]] = None) -> LLMAnalysis:
        """
        Fallback analysis when LLM fails
        """
        query_lower = query.lower()

        # Simple rule-based intent detection
        intent = LLMIntent.GENERAL
        category_mentioned = None
        source_mentioned = None
        keywords = query.split()

        # Check for category mentions
        for category in self.available_categories:
            if category.lower() in query_lower:
                intent = LLMIntent.CATEGORY
                category_mentioned = category
                break

        # Check for source mentions
        for source in self.available_sources:
            if source.lower() in query_lower:
                intent = LLMIntent.SOURCE
                source_mentioned = source
                break

        # Check for location keywords
        location_keywords = ["near", "nearby", "around", "local", "close"]
        if any(keyword in query_lower for keyword in location_keywords) and user_location:
            intent = LLMIntent.NEARBY

        # Check for quality keywords
        quality_keywords = ["best", "top", "high quality", "relevant", "important"]
        if any(keyword in query_lower for keyword in quality_keywords):
            intent = LLMIntent.SCORE

        return LLMAnalysis(
            original_query=query,
            intent=intent,
            entities=[],
            keywords=keywords,
            location_mentioned=None,
            category_mentioned=category_mentioned,
            source_mentioned=source_mentioned,
            confidence=0.6,
            reasoning="Fallback rule-based analysis"
        )

    async def process_query_intelligently(self, query: str,
                                          user_location: Optional[Dict[str, float]] = None) -> QueryProcessingResponse:
        """
        Process query and determine the best search strategy
        """
        try:
            # Analyze the query
            analysis = await self.analyze_query(query, user_location)

            # Determine endpoint and parameters based on analysis
            endpoint, parameters = self._determine_search_strategy(analysis, user_location)

            return QueryProcessingResponse(
                analysis=analysis,
                suggested_endpoint=endpoint,
                query_parameters=parameters,
                fallback_strategy="search" if endpoint != "search" else "category"
            )

        except Exception as e:
            logger.error(f"Error processing query intelligently: {e}")
            # Return fallback response
            return QueryProcessingResponse(
                analysis=self._fallback_query_analysis(query, user_location),
                suggested_endpoint="search",
                query_parameters={"query": query, "limit": 5},
                fallback_strategy="category"
            )

    def _determine_search_strategy(self, analysis: LLMAnalysis, user_location: Optional[Dict[str, float]]) -> Tuple[
        str, Dict[str, Any]]:
        """
        Determine the best search strategy based on LLM analysis
        """
        intent = analysis.intent
        parameters = {"limit": 5}

        # Enhanced fallback logic for GENERAL intent
        if intent == LLMIntent.GENERAL:
            # Check if query contains category keywords
            query_lower = analysis.original_query.lower()

            # Category detection
            for category in self.available_categories:
                if category.lower() in query_lower:
                    return "category", {**parameters, "category": category}

            # Source detection
            for source in self.available_sources:
                if source.lower() in query_lower:
                    return "source", {**parameters, "source": source}

            # Location keywords detection
            location_keywords = ["near", "nearby", "around", "local", "close"]
            if any(keyword in query_lower for keyword in location_keywords) and user_location:
                return "nearby", {
                    **parameters,
                    "lat": user_location["lat"],
                    "lon": user_location["lon"],
                    "radius": 10.0
                }

            # Quality keywords detection
            quality_keywords = ["best", "top", "high quality", "relevant", "important"]
            if any(keyword in query_lower for keyword in quality_keywords):
                return "score", {**parameters, "min_score": 0.7}

            # Default to text search for GENERAL intent
            return "search", {**parameters, "query": analysis.original_query}

        elif intent == LLMIntent.CATEGORY and analysis.category_mentioned:
            return "category", {**parameters, "category": analysis.category_mentioned}

        elif intent == LLMIntent.SOURCE and analysis.source_mentioned:
            return "source", {**parameters, "source": analysis.source_mentioned}

        elif intent == LLMIntent.NEARBY and user_location:
            return "nearby", {
                **parameters,
                "lat": user_location["lat"],
                "lon": user_location["lon"],
                "radius": 10.0
            }

        elif intent == LLMIntent.SCORE:
            return "score", {**parameters, "min_score": 0.7}

        elif intent == LLMIntent.SEARCH or analysis.keywords:
            search_query = " ".join(analysis.keywords) if analysis.keywords else analysis.original_query
            return "search", {**parameters, "query": search_query}

        else:
            # Final fallback to search
            return "search", {**parameters, "query": analysis.original_query}

    async def health_check(self) -> bool:
        """
        Check if the OpenAI service is working
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                temperature=0.1
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"LLM service health check failed: {e}")
            return False