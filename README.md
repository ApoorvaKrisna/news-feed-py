# Contextual News Data Retrieval System

A sophisticated backend system that fetches and organizes news articles with LLM-powered insights and contextual understanding.

## Features

- 🧠 **LLM Integration**: Uses OpenAI GPT to extract entities and understand user intent
- 📊 **Multiple Search Strategies**: Category, score, search, source, and location-based retrieval
- 🌍 **Location-Aware**: Geospatial queries with distance calculations
- 📈 **Trending News**: Location-based trending feed with simulated user engagement
- 🚀 **FastAPI Backend**: High-performance async API with automatic documentation
- 🗄️ **MongoDB Integration**: Efficient document storage and retrieval
- 🎨 **Simple UI**: Basic web interface for API demonstration

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **LLM**: OpenAI GPT API
- **Frontend**: HTML/CSS/JavaScript
- **Caching**: Redis (optional)

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd contextual-news-system
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `MONGODB_URL`: Your MongoDB connection string
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_NAME`: MongoDB database name
- `COLLECTION_NAME`: MongoDB collection name

### 3. Database Setup

Ensure your MongoDB instance is running and contains the news articles collection with the following structure:

```json
{
  "id": "unique-article-id",
  "title": "Article Title",
  "description": "Article Description",
  "url": "https://example.com/article",
  "publication_date": "2024-01-01T00:00:00",
  "source_name": "News Source",
  "category": ["Category1", "Category2"],
  "relevance_score": 0.85,
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

### 4. Run the Application

```bash
python -m uvicorn app.main:app --reload
```

The application will be available at:
- **API Documentation**: http://localhost:8000/docs
- **Web Interface**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Core News Endpoints

- `POST /api/v1/news/query` - Intelligent query processing with LLM
- `GET /api/v1/news/category` - Category-based search
- `GET /api/v1/news/score` - Relevance score based retrieval
- `GET /api/v1/news/search` - Text search in titles and descriptions
- `GET /api/v1/news/source` - Source-based retrieval
- `GET /api/v1/news/nearby` - Location-based search

### Trending News

- `GET /api/v1/trending` - Location-based trending news feed

### Example Usage

```bash
# Intelligent query processing
curl -X POST "http://localhost:8000/api/v1/news/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Latest tech news from Silicon Valley", "user_lat": 37.4220, "user_lon": -122.0840}'

# Category search
curl "http://localhost:8000/api/v1/news/category?category=Technology&limit=5"

# Nearby news
curl "http://localhost:8000/api/v1/news/nearby?lat=37.4220&lon=-122.0840&radius=10&limit=5"

# Trending news
curl "http://localhost:8000/api/v1/trending?lat=37.4220&lon=-122.0840&limit=10"
```

## Project Structure

```
contextual-news-system/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic services
│   ├── api/v1/              # API endpoints
│   ├── utils/               # Utility functions
│   └── static/              # Frontend files
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

The project follows Python best practices:
- Type hints throughout
- Async/await patterns
- Proper error handling
- Comprehensive logging
- Input validation

## Deployment

The application is designed for easy deployment on free hosting platforms:
- Configure environment variables
- Install dependencies
- Run with uvicorn

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is created for demonstration purposes.