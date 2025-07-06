# Contextual News Retrieval Backend

This is a backend system for retrieving and enriching news data using LLMs and MongoDB.

## Features
- OpenAI-based entity + intent extraction
- MongoDB article retrieval
- Filtering: by category, source, score, search keyword, nearby location
- Haversine-based sorting

## Setup

```bash
git clone <your-repo-url>
cd contextual-news-backend
cp .env.example .env
pip install -r requirements.txt
python run.py
