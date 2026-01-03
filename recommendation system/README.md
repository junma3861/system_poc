# 🤖 AI-Powered Recommendation System

**Intelligent product recommendations with natural language chat interface**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A production-ready recommendation system combining collaborative filtering, natural language understanding, and conversation memory for personalized product discovery.

## 📍 Navigation

- **New here?** → [GETTING_STARTED.md](GETTING_STARTED.md) - Complete setup guide
- **Want features?** → You're reading it! (README.md)
- **Using Docker?** → [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Docker tips & commands
- **Deploying to AWS?** → [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) - Production guide
- **Understanding memory?** → [MEMORY_MANAGEMENT.md](MEMORY_MANAGEMENT.md) - Memory system
- **Exploring code?** → [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Code organization

[🚀 Quick Start](#quick-start) • [📖 Features](#features) • [🐳 Docker](#docker-deployment) • [☁️ AWS](#aws-deployment) • [🧪 Demo](#demo)

---

## ✨ Features

### 🤖 AI Chatbot Search Engine (NEW)
- **Natural Language Understanding**: Powered by OpenAI GPT models
- **Intelligent Query Processing**: Understands user intent, extracts categories, price ranges, and keywords
- **Personalized Search**: Combines query understanding with user's shopping history
- **Conversational Interface**: Natural, friendly responses to user queries
- **Smart Recommendations**: Integrates collaborative filtering with search
- **Memory Management**: Maintains conversation context across sessions (short-term & long-term)

### 📊 Recommendation Engine
- **User-based Collaborative Filtering**: Recommendations based on similar users' preferences
- **Item-based Collaborative Filtering**: Recommendations based on similar products
- **Similar Users Discovery**: Find users with similar purchase patterns
- **Similar Products**: Find products frequently purchased together
- **User Analytics**: Purchase statistics and behavior insights

### 🚀 Production Ready
- **RESTful API**: Fast, scalable FastAPI service
- **Docker Support**: One-command deployment
- **AWS Ready**: ECS Fargate deployment scripts included
- **Interactive Documentation**: Automatic Swagger UI and ReDoc
- **CORS Support**: Cross-origin requests enabled

---

## 🚀 Quick Start

**Choose your preferred method:**

### Option 1: Docker (Recommended - 3 commands)

```bash
docker-compose up -d                    # Start all services
docker-compose exec app python example.py  # Load sample data
open http://localhost:8000/index.html   # Open web interface
```

**Done!** All services running (FastAPI, PostgreSQL, MongoDB, Redis)

### Option 2: Local Development

```bash
# 1. Install databases (macOS)
brew install postgresql@14 mongodb-community redis
brew services start postgresql@14 mongodb-community redis

# 2. Setup Python environment
pip install -r requirements.txt
createdb recommendation_db

# 3. Configure
cp .env.example .env
# Edit .env with your OpenAI API key

# 4. Initialize data
python example.py

# 5. Start server
uvicorn main:app --reload
```

**📖 Detailed Setup:** See [GETTING_STARTED.md](GETTING_STARTED.md) for complete instructions

---

## 🎯 Demo

### Try These Queries

```bash
# AI Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me affordable laptops under $500", "user_id": 1}'

# Get Recommendations
curl http://localhost:8000/recommend/user/1?n_recommendations=5

# Product Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "running shoes", "user_id": 1}'
```

### Web Interface

Open http://localhost:8000/index.html for the full interactive experience:
- 💬 AI chat interface
- 🔍 Product search
- 🧠 Conversation memory
- 🎯 Personalized recommendations

---

## 🏗️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Backend** | FastAPI, Python 3.11+ |
| **AI/ML** | OpenAI GPT-4o-mini, Scikit-learn |
| **Databases** | PostgreSQL (products), MongoDB (history), Redis (cache) |
| **ORM** | SQLAlchemy, PyMongo |
| **Deployment** | Docker, Docker Compose, AWS ECS Fargate |

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | Complete setup guide (Docker, Local, AWS) |
| [MEMORY_MANAGEMENT.md](MEMORY_MANAGEMENT.md) | Memory system architecture & API |
| [DOCKER_GUIDE.md](DOCKER_GUIDE.md) | Docker tips, commands & troubleshooting |
| [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) | Production AWS deployment guide |

---

## 🐳 Docker Deployment

### Quick Start

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec app python example.py

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### What's Included

- ✅ FastAPI application
- ✅ PostgreSQL 14 (products & users)
- ✅ MongoDB 7 (conversation history)
- ✅ Redis 7 (session cache)
- ✅ Health checks for all services
- ✅ Volume persistence
- ✅ Automated initialization

**See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for advanced usage**

---

## ☁️ AWS Deployment

Deploy to production with ECS Fargate:

```bash
# 1. Push to ECR
./deploy-ecr.sh

# 2. Create infrastructure
./setup-aws-infrastructure.sh

# 3. Deploy service
# See AWS_DEPLOYMENT.md for complete steps
```

**Estimated cost:** $140-435/month

**See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for complete guide**

---

## 🔌 API Endpoints

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | AI-powered conversational search |
| `/search` | POST | Intelligent product search |
| `/recommend/user/{user_id}` | GET | User-based recommendations |
| `/recommend/item/{item_id}` | GET | Item-based recommendations |
| `/memory/conversation/{user_id}` | GET | Get conversation history |
| `/memory/preferences/{user_id}` | GET | Extract user preferences |
| `/health` | GET | Health check |

### Example Requests

**Chat with AI:**
```bash
POST /chat
{
  "query": "Show me affordable laptops under $500",
  "user_id": 1,
  "session_id": "session_123",
  "n_results": 5
}
```

**Get Recommendations:**
```bash
GET /recommend/user/1?n_recommendations=5&method=user-based
```

**Search Products:**
```bash
POST /search
{
  "query": "running shoes Nike",
  "user_id": 1,
  "n_results": 10
}
```

**View Conversation History:**
```bash
GET /memory/conversation/1?days=7
```

---

## 🧠 How It Works

### 1. Natural Language Understanding
- OpenAI GPT-4o-mini extracts intent, categories, price ranges, keywords
- Understands follow-up questions using conversation context

### 2. Intelligent Search
- Combines NLP understanding with product catalog
- Applies filters: category, price range, brand, keywords
- Ranks by relevance and personalization score

### 3. Collaborative Filtering
- **User-based**: Finds similar users, recommends their purchases
- **Item-based**: Finds similar products based on co-purchase patterns
- Combines with search results for personalized ranking

### 4. Memory Management
- **Short-term**: Redis stores active conversations (1hr TTL)
- **Long-term**: MongoDB stores complete history
- **Context**: Last 3-5 messages sent to LLM for continuity

---

## 🧪 Testing

### Automated Tests

```bash
# Test chatbot features
python test_chatbot.py

# Test memory system
python test_memory.py

# Test API endpoints
python test_api.py
```

### Sample Queries

Try these in the chat interface:

```
"Show me affordable electronics"
"I need Nike running shoes under $100"
"Find luxury products from Apple"
"Recommend products based on my history"
"Show me more expensive ones"  # Context-aware follow-up
```

---

## 📁 Project Structure

```
recommendation-system/
├── main.py                      # FastAPI application
├── recommendation_engine.py     # Core recommendation logic
├── config/
│   └── database.py             # Database connections
├── models/
│   └── schemas.py              # Data models & API schemas
├── services/
│   ├── chatbot.py              # NLP query processing
│   ├── search_engine.py        # Intelligent search
│   ├── memory.py               # Conversation memory
│   ├── collaborative_filtering.py  # CF algorithms
│   └── data_loader.py          # Data utilities
├── index.html                   # Web UI
├── Dockerfile                   # Container image
├── docker-compose.yml          # Multi-service orchestration
├── deploy-ecr.sh               # AWS ECR deployment
├── setup-aws-infrastructure.sh # AWS setup automation
└── ecs-task-definition.json   # ECS configuration
```

## Architecture

### Databases
- **User Profile (SQL)**: Stores user demographic and account information
- **Product (SQL)**: Contains product catalog with details
- **User Purchase History (MongoDB)**: Stores transaction data (ideal for flexible, document-based purchase records with varying attributes)

### Algorithm
- **Collaborative Filtering**: Implements both user-based and item-based approaches
  - User-based: Recommends products liked by similar users
  - Item-based: Recommends products similar to those the user has purchased

### Project Structure
```
recommendation-system/
├── main.py                      # FastAPI application with chatbot endpoints
├── recommendation_engine.py     # Main recommendation engine
├── config/
│   └── database.py             # Database connections + OpenAI config
├── models/
│   └── schemas.py              # SQLAlchemy, MongoDB schemas + API models
├── services/
│   ├── data_loader.py          # Data loading utilities
│   ├── collaborative_filtering.py  # CF algorithms
│   ├── chatbot.py              # NLP query processor with OpenAI
│   └── search_engine.py        # Intelligent search combining query + history
├── test_chatbot.py             # Test script for chatbot features
├── requirements.txt            # Python dependencies
└── .env.example                # Environment variables template
```

## Testing the API

### Using the Test Script

```bash
python test_chatbot.py
```

This comprehensive test script covers:
- Chatbot natural language queries
- Search with personalization
- Conversation suggestions
- Various query types and intents

### Using curl

```bash
# Chat with AI assistant
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me affordable laptops", "user_id": 1}'

# Intelligent search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "running shoes under $100", "user_id": 1}'

# Get suggestions
curl http://localhost:8000/chat/suggestions?user_id=1

# Get recommendations (traditional endpoint)
curl http://localhost:8000/recommendations/1

# Get similar users
curl http://localhost:8000/users/1/similar

# Get user statistics
curl http://localhost:8000/users/1/statistics
```

### Using Python requests

```python
import requests

# Get recommendations
response = requests.get(
    "http://localhost:8000/recommendations/1",
    params={"method": "user-based", "n_recommendations": 5}
)
print(response.json())
```

---

## ⚙️ Configuration

### Environment Variables

```env
# PostgreSQL
SQL_DATABASE_URL=postgresql://user@localhost:5432/recommendation_db

# MongoDB (optional)
MONGO_URI=mongodb://localhost:27017/

# Redis (optional)
REDIS_HOST=localhost

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Memory
SESSION_TTL=3600
MAX_CONTEXT_MESSAGES=10
```

---

## 🚀 Performance

- **Response Time**: < 200ms for cached recommendations
- **Throughput**: 1000+ req/s (with 4 workers)
- **Caching**: Similarity matrices precomputed
- **Async**: FastAPI handles concurrent requests efficiently
- **Indexing**: Optimized database indexes on user_id, product_id

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check if databases are running: `docker-compose ps` |
| No recommendations | Ensure user has purchase history, run `python example.py` |
| OpenAI errors | Verify API key in `.env` file |
| Port in use | Stop conflicting services or change port in docker-compose.yml |

**Detailed troubleshooting:** [GETTING_STARTED.md](GETTING_STARTED.md#troubleshooting)

---

## 📝 License

MIT License

---

**Built with ❤️ using FastAPI, OpenAI, and modern ML techniques**
