from pydantic_settings import BaseSettings
from typing import Optional
import os
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # App settings
    app_name: str = "Contextual News Data Retrieval System"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "production")

    # API settings
    api_v1_prefix: str = "/api/v1"

    # MongoDB Atlas settings
    mongo_user: str = os.getenv("MONGO_USER", "")
    mongo_pass: str = os.getenv("MONGO_PASS", "")
    mongo_cluster: str = os.getenv("MONGO_CLUSTER", "")
    mongo_db: str = os.getenv("MONGO_DB", "newsdb")

    # Collection name
    collection_name: str = os.getenv("COLLECTION_NAME", "articles")

    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # LLM settings
    max_tokens: int = 500
    temperature: float = 0.3

    # Pagination settings
    default_page_size: int = 10
    max_page_size: int = 100

    # Location settings
    default_radius_km: float = 10.0
    max_radius_km: float = 100.0

    # Trending settings
    trending_cache_ttl: int = 300  # 5 minutes
    trending_default_limit: int = 10

    # Redis settings (for caching)
    redis_url: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379")

    # CORS settings
    allowed_origins: list = ["*"]
    allowed_methods: list = ["*"]
    allowed_headers: list = ["*"]

    @property
    def mongodb_url(self) -> str:
        """Generate MongoDB Atlas connection URL with proper encoding"""
        if not all([self.mongo_user, self.mongo_pass, self.mongo_cluster]):
            raise ValueError("MongoDB credentials (MONGO_USER, MONGO_PASS, MONGO_CLUSTER) are required")

        encoded_user = urllib.parse.quote_plus(self.mongo_user)
        encoded_pass = urllib.parse.quote_plus(self.mongo_pass)

        return f"mongodb+srv://{encoded_user}:{encoded_pass}@{self.mongo_cluster}/?retryWrites=true&w=majority"

    @property
    def database_name(self) -> str:
        """Return the database name"""
        return self.mongo_db

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Validation
if not settings.openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

if not all([settings.mongo_user, settings.mongo_pass, settings.mongo_cluster]):
    raise ValueError("MongoDB Atlas credentials (MONGO_USER, MONGO_PASS, MONGO_CLUSTER) are required")