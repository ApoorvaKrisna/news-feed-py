# Contextual News Retrieval Backend

This is a backend system for retrieving and enriching news data using LLMs and MongoDB.

## Features
- OpenAI-based entity + intent extraction
- MongoDB article retrieval
- Filtering: by category, source, score, search keyword, nearby location
- Haversine-based sorting

## Setup

```bash
git clone https://github.com:ApoorvaKrisna/news-feed-py.git
cd contextual-news-backend
cp .env.example .env
pip install -r requirements.txt
python run.py
