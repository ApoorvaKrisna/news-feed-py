from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

from app.config import settings
from app.services.database import DatabaseService
from app.services.llm_service import LLMService
from app.api.v1 import news, trending

# Global service instances
db_service = DatabaseService()
llm_service = LLMService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up the application...")
    try:
        await db_service.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down the application...")
    await db_service.disconnect()
    logger.info("Database disconnected")


# Production-ready main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
from loguru import logger

from app.config import settings
from app.services.database import DatabaseService
from app.services.llm_service import LLMService
from app.api.v1 import news, trending

# Global service instances
db_service = DatabaseService()
llm_service = LLMService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up the application...")
    try:
        await db_service.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down the application...")
    await db_service.disconnect()
    logger.info("Database disconnected")


# Initialize FastAPI app with production settings
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A contextual news data retrieval system with LLM integration",
    lifespan=lifespan,
    # Production optimizations
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routers
app.include_router(
    news.router,
    prefix=settings.api_v1_prefix,
    tags=["news"]
)

app.include_router(
    trending.router,
    prefix=settings.api_v1_prefix,
    tags=["trending"]
)


# Root endpoint
@app.get("/")
async def root():
    return FileResponse("app/static/index.html")


# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    try:
        await db_service.ping()
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "database": "connected",
            "environment": "production" if not settings.debug else "development"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# Production server entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disabled in production
        log_level="info"
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API routers
app.include_router(
    news.router,
    prefix=settings.api_v1_prefix,
    tags=["news"]
)

app.include_router(
    trending.router,
    prefix=settings.api_v1_prefix,
    tags=["trending"]
)


# Root endpoint
@app.get("/")
async def root():
    return FileResponse("app/static/index.html")


# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        await db_service.ping()
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)