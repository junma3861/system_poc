# 📂 Project Structure

## Overview

```
recommendation-system/
├── 📱 Frontend
│   └── index.html                   # Web UI (chat, search, memory, recommendations)
│
├── 🚀 Backend
│   ├── main.py                      # FastAPI application & API endpoints
│   ├── recommendation_engine.py     # Core recommendation algorithms
│   │
│   ├── config/
│   │   └── database.py              # Database connections (PostgreSQL, MongoDB)
│   │
│   ├── models/
│   │   └── schemas.py               # Data models & API request/response schemas
│   │
│   └── services/
│       ├── chatbot.py               # AI chat & NLP query processing
│       ├── search_engine.py         # Intelligent product search
│       ├── memory.py                # Conversation memory (Redis + MongoDB)
│       ├── collaborative_filtering.py  # Recommendation algorithms
│       └── data_loader.py           # Data loading utilities
│
├── 🐳 Deployment
│   ├── Dockerfile                   # Container image definition
│   ├── docker-compose.yml           # Multi-service orchestration
│   ├── .dockerignore                # Docker build exclusions
│   ├── deploy-ecr.sh                # AWS ECR deployment script
│   ├── setup-aws-infrastructure.sh  # AWS resource creation
│   └── ecs-task-definition.json    # ECS Fargate configuration
│
├── 🧪 Testing & Examples
│   ├── example.py                   # Sample data & DB initialization
│   ├── test_chatbot.py             # Chatbot feature tests
│   ├── test_memory.py              # Memory system tests
│   └── test_api.py                 # API endpoint tests
│
├── ⚙️ Configuration
│   ├── .env                        # Environment variables (not in git)
│   ├── .env.example                # Environment template
│   ├── requirements.txt            # Python dependencies
│   └── .gitignore                  # Git exclusions
│
├── 🛠️ Setup & Utilities
│   └── setup.sh                    # Complete system setup script
│
└── 📖 Documentation
    ├── README.md                    # Main documentation & feature overview
    ├── GETTING_STARTED.md          # Setup guide (Docker, Local, AWS)
    ├── MEMORY_MANAGEMENT.md        # Memory system architecture
    ├── DOCKER_GUIDE.md             # Docker usage & commands
    └── AWS_DEPLOYMENT.md           # Production deployment guide
```

---

## 📱 Frontend

### `index.html` (800+ lines)
- **Purpose**: Full-featured web interface
- **Features**: 
  - 💬 Chat tab with AI assistant
  - 🔍 Product search interface
  - 🧠 Memory management (view history, preferences)
  - 🎯 Personalized recommendations
  - 📊 Real-time statistics
- **Tech**: Vanilla JavaScript, modern CSS with gradients
- **Usage**: Open directly in browser or via `http://localhost:8000/index.html`

---

## 🚀 Backend

### `main.py` (400+ lines)
- **Purpose**: FastAPI application & API route definitions
- **Key Endpoints**:
  - `POST /chat` - AI-powered chat
  - `POST /search` - Product search
  - `GET /recommend/user/{id}` - User recommendations
  - `GET /recommend/item/{id}` - Similar products
  - `GET /memory/*` - Memory management
- **Startup**: Initializes databases, loads data, starts memory services

### `recommendation_engine.py` (300+ lines)
- **Purpose**: Core recommendation logic
- **Algorithms**:
  - User-based collaborative filtering
  - Item-based collaborative filtering
  - Similarity computation (cosine similarity)
- **Data**: Manages user-item matrices, similarity matrices

### Services

#### `services/chatbot.py` (280+ lines)
- **Purpose**: Natural language processing & chat logic
- **Key Functions**:
  - `process_query()` - Analyze user intent with OpenAI
  - `generate_response()` - Create conversational responses
- **Features**: Intent extraction, category detection, price range parsing

#### `services/search_engine.py` (350+ lines)
- **Purpose**: Intelligent product search combining NLP + recommendations
- **Key Functions**:
  - `search()` - Main search orchestration
  - `filter_products()` - Apply category, price, brand filters
  - `rank_results()` - Personalization scoring
- **Scoring**: Combines relevance + personalization (70/30 split)

#### `services/memory.py` (340+ lines)
- **Purpose**: Two-tier conversation memory system
- **Key Functions**:
  - `add_message()` - Store in Redis + MongoDB
  - `get_conversation_context()` - Load recent messages
  - `get_user_preferences()` - Extract categories, brands, keywords
- **Storage**: 
  - Short-term: Redis (1 hour TTL)
  - Long-term: MongoDB (persistent)

#### `services/collaborative_filtering.py` (150+ lines)
- **Purpose**: Recommendation algorithm implementations
- **Methods**:
  - `get_recommendations()` - User or item-based CF
  - `get_similar_users()` - Find users with similar taste
  - `get_similar_items()` - Find similar products
- **Tech**: Scikit-learn cosine similarity, sparse matrices

#### `services/data_loader.py` (100+ lines)
- **Purpose**: Load data from databases
- **Functions**:
  - `load_users()` - From PostgreSQL
  - `load_products()` - From PostgreSQL
  - `load_purchase_history()` - From MongoDB

### Configuration

#### `config/database.py` (80+ lines)
- **Purpose**: Database connection management
- **Connections**:
  - SQLAlchemy engine (PostgreSQL)
  - MongoDB client
  - Redis client (optional)
- **Features**: Connection pooling, error handling

### Models

#### `models/schemas.py` (200+ lines)
- **Purpose**: Data models for database & API
- **SQLAlchemy Models**:
  - `User` - User profiles
  - `Product` - Product catalog
- **Pydantic Models**:
  - `ChatRequest/Response` - Chat API
  - `SearchRequest/Response` - Search API
  - `RecommendationResponse` - Recommendation API
  - `MemoryResponse` - Memory API

---

## 🐳 Deployment

### Docker Files

#### `Dockerfile` (35 lines)
- **Base**: python:3.11-slim
- **Layers**:
  1. System dependencies (gcc, postgresql-client)
  2. Python packages
  3. Application code
- **Health Check**: curl localhost:8000/health
- **Port**: 8000

#### `docker-compose.yml` (120 lines)
- **Services**:
  - `app` - FastAPI application
  - `postgres` - PostgreSQL 14
  - `mongodb` - MongoDB 7
  - `redis` - Redis 7
- **Features**: Health checks, volume persistence, networking

### AWS Deployment Scripts

#### `deploy-ecr.sh` (100 lines)
- **Purpose**: Push Docker image to AWS ECR
- **Steps**:
  1. Validate AWS CLI
  2. Create/verify ECR repository
  3. Authenticate Docker to ECR
  4. Build, tag, push image
- **Output**: ECR image URI

#### `setup-aws-infrastructure.sh` (200 lines)
- **Purpose**: Create AWS resources
- **Creates**:
  - CloudWatch log groups
  - Secrets Manager secret (OpenAI key)
  - VPC & security groups
  - ECS cluster
  - IAM roles
- **Usage**: Run before deploying ECS service

#### `ecs-task-definition.json` (120 lines)
- **Purpose**: ECS Fargate task configuration
- **Specs**: 1 vCPU, 2GB RAM
- **Environment**: Database URLs, API keys
- **Logging**: CloudWatch logs

---

## 🧪 Testing & Examples

### `example.py` (200 lines)
- **Purpose**: Create sample data & initialize database
- **Creates**:
  - 10 users with profiles
  - 15 products across categories
  - 38 realistic purchases
- **Demo**: Shows recommendation engine in action

### `test_chatbot.py` (150 lines)
- **Tests**:
  - Chat with various query types
  - Search functionality
  - Conversation suggestions
  - Intent detection

### `test_memory.py` (120 lines)
- **Tests**:
  - Session management
  - Conversation history
  - Preference extraction
  - Context awareness

### `test_api.py` (100 lines)
- **Tests**:
  - All API endpoints
  - Error handling
  - Response validation

---

## ⚙️ Configuration

### `.env` (not in git)
```env
# PostgreSQL
SQL_DATABASE_URL=postgresql://user@localhost:5432/recommendation_db

# MongoDB
MONGO_URI=mongodb://localhost:27017/
MONGO_DATABASE=recommendation_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Memory
SESSION_TTL=3600
MAX_CONTEXT_MESSAGES=10
```

### `requirements.txt` (25 packages)
- **Web**: fastapi, uvicorn, python-multipart
- **Database**: sqlalchemy, psycopg2-binary, pymongo, redis
- **AI/ML**: openai, scikit-learn, pandas, numpy
- **Utils**: python-dotenv, pydantic

---

## 🛠️ Setup Scripts

### `setup.sh` (300 lines)
- **Purpose**: One-command complete setup
- **Installs**:
  - PostgreSQL (required)
  - MongoDB (optional)
  - Redis (optional)
- **Configures**:
  - Creates database
  - Sets up .env file
  - Installs Python packages
  - Loads sample data
- **OS Support**: macOS, Linux

---

## 📖 Documentation

### `README.md` (400 lines)
- **Sections**:
  - Features overview
  - Quick start (3 options)
  - API reference
  - Tech stack
  - Configuration

### `GETTING_STARTED.md` (700 lines)
- **Complete setup guide**:
  - Option 1: Docker (recommended)
  - Option 2: Local development
  - Option 3: AWS cloud
- **Includes**: Troubleshooting, sample data, testing

### `MEMORY_MANAGEMENT.md` (400 lines)
- **Deep dive on memory system**:
  - Architecture (Redis + MongoDB)
  - API endpoints
  - Configuration
  - Usage examples

### `DOCKER_GUIDE.md` (500 lines)
- **Docker usage**:
  - docker-compose commands
  - Development workflow
  - Troubleshooting
  - Production optimization

### `AWS_DEPLOYMENT.md` (400 lines)
- **Production deployment**:
  - Complete AWS setup
  - Cost estimation
  - Monitoring & logging
  - CI/CD pipeline examples

---

## 🔍 Finding Code

### Need to modify...

**Chat behavior?**
→ `services/chatbot.py`

**Search logic?**
→ `services/search_engine.py`

**Recommendations?**
→ `recommendation_engine.py` or `services/collaborative_filtering.py`

**Memory management?**
→ `services/memory.py`

**API endpoints?**
→ `main.py`

**Database models?**
→ `models/schemas.py`

**UI appearance?**
→ `index.html` (CSS in `<style>` tag)

**Docker configuration?**
→ `docker-compose.yml` or `Dockerfile`

**AWS deployment?**
→ `deploy-ecr.sh`, `setup-aws-infrastructure.sh`, `ecs-task-definition.json`

---

## 📊 Code Statistics

| Component | Files | Lines of Code |
|-----------|-------|---------------|
| Backend (Python) | 10 | ~2,500 |
| Frontend (HTML/JS) | 1 | ~800 |
| Deployment | 5 | ~600 |
| Tests | 3 | ~400 |
| Documentation | 5 | ~2,500 |
| **Total** | **24** | **~6,800** |

---

## 🚀 Quick Navigation

- **Start here**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **Understand features**: [README.md](README.md)
- **Deploy with Docker**: [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- **Deploy to AWS**: [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)
- **Memory system**: [MEMORY_MANAGEMENT.md](MEMORY_MANAGEMENT.md)
- **Code structure**: You're reading it! 📖
