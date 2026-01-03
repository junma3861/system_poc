# 🚀 Getting Started - Recommendation System

**Choose your deployment method:**

- [Option 1: Docker (Recommended)](#option-1-docker-recommended) - Fastest setup, everything included
- [Option 2: Local Development](#option-2-local-development) - For development and customization
- [Option 3: AWS Cloud](#option-3-aws-cloud-deployment) - Production deployment

---

## Option 1: Docker (Recommended)

**⚡ Fastest way to get started - everything included!**

### Prerequisites
- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- 4GB RAM available
- 10GB disk space

### Quick Start (3 steps)

```bash
# 1. Start all services
docker-compose up -d

# 2. Initialize database with sample data
docker-compose exec app python example.py

# 3. Open in browser
open http://localhost:8000/index.html
```

**That's it!** 🎉 All services are running:
- FastAPI app: http://localhost:8000
- PostgreSQL: localhost:5432
- MongoDB: localhost:27017
- Redis: localhost:6379

### Add Your OpenAI Key (Optional)

For full AI chat features:

```bash
# 1. Edit .env file
nano .env

# 2. Add your key
OPENAI_API_KEY=sk-your-key-here

# 3. Restart
docker-compose restart app
```

### Useful Commands

```bash
# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Reset everything (removes data)
docker-compose down -v
docker-compose up -d

# Access container shell
docker-compose exec app bash
```

**Next:** Try the [Quick Test](#quick-test) section below!

---

## Option 2: Local Development

**For developers who want to customize and develop locally.**

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- MongoDB 7+ (optional, but recommended)
- Redis 7+ (optional, but recommended)

### Step-by-Step Setup

#### 1. Install Databases

**macOS:**
```bash
# PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# MongoDB (optional)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Redis (optional)
brew install redis
brew services start redis
```

**Linux:**
```bash
# PostgreSQL
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# MongoDB (optional)
sudo apt-get install mongodb
sudo systemctl start mongodb

# Redis (optional)
sudo apt-get install redis-server
sudo systemctl start redis
```

**Or use our automated script:**
```bash
chmod +x setup_databases.sh
./setup_databases.sh
```

#### 2. Create Python Environment

```bash
# Using conda
conda create -n recommendation_system python=3.11
conda activate recommendation_system

# Or using venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

#### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimum configuration (.env):**
```env
# PostgreSQL (required)
SQL_DATABASE_URL=postgresql://your_username@localhost:5432/recommendation_db

# OpenAI (optional, for AI features)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# MongoDB (optional, for conversation history)
MONGO_URI=mongodb://localhost:27017/
MONGO_DATABASE=recommendation_db

# Redis (optional, for session memory)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**Note:** On macOS, PostgreSQL uses your system username by default (no password needed).

#### 5. Create Database

```bash
# Create the database
createdb recommendation_db

# Or using psql
psql postgres
CREATE DATABASE recommendation_db;
\q
```

#### 6. Initialize with Sample Data

```bash
python example.py
```

This creates tables and loads sample data:
- 10 users
- 15 products  
- 38 purchases

#### 7. Start the Server

```bash
# Development mode (auto-reload)
uvicorn main:app --reload

# Or with Python
python main.py
```

**Server running at:** http://localhost:8000

#### 8. Open the Web Interface

```bash
# Open in browser
open index.html

# Or navigate to
open http://localhost:8000/docs  # API documentation
```

**Next:** Try the [Quick Test](#quick-test) section below!

---

## Option 3: AWS Cloud Deployment

**Deploy to production on AWS ECS Fargate.**

### Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Docker installed
- OpenAI API key

### Deployment Steps

#### 1. Configure AWS

```bash
# Configure AWS credentials
aws configure

# Set your region
export AWS_REGION=us-east-1
```

#### 2. Push Docker Image to ECR

```bash
# Make script executable
chmod +x deploy-ecr.sh

# Run deployment
./deploy-ecr.sh
```

This will:
- Create ECR repository
- Build Docker image
- Push to AWS ECR
- Output image URI

#### 3. Create AWS Infrastructure

```bash
# Make script executable
chmod +x setup-aws-infrastructure.sh

# Run infrastructure setup
./setup-aws-infrastructure.sh
```

This creates:
- CloudWatch log groups
- Secrets Manager secret (for OpenAI key)
- VPC and security groups
- ECS cluster
- IAM roles

#### 4. Set Up Managed Databases (Choose One)

**Option A: AWS Managed Services** (Recommended for production)

```bash
# RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier recommendation-db \
  --db-instance-class db.t3.small \
  --engine postgres \
  --master-username admin \
  --master-user-password your_password \
  --allocated-storage 20

# DocumentDB (MongoDB compatible)
aws docdb create-db-cluster \
  --db-cluster-identifier recommendation-docdb \
  --engine docdb \
  --master-username admin \
  --master-user-password your_password

# ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id recommendation-redis \
  --engine redis \
  --cache-node-type cache.t3.micro \
  --num-cache-nodes 1
```

**Option B: Docker Compose Databases** (For testing/development)

Keep using the databases from docker-compose, but ensure they're accessible from ECS.

#### 5. Update ECS Task Definition

Edit `ecs-task-definition.json` with your values:
- AWS account ID
- AWS region
- Database endpoints from step 4
- ECR image URI from step 2

#### 6. Deploy ECS Service

```bash
# Register task definition
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster recommendation-cluster \
  --service-name recommendation-service \
  --task-definition recommendation-app \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

#### 7. Access Your Application

```bash
# Get task public IP
aws ecs list-tasks --cluster recommendation-cluster
aws ecs describe-tasks --cluster recommendation-cluster --tasks <task-arn>
```

Access at: `http://<public-ip>:8000`

**For detailed AWS deployment instructions, see:** [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)

**Estimated Monthly Cost:** $140-435 (varies by usage)

---

## Quick Test

Once your system is running, test these features:

### 1. Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","message":"Service is operational"}
```

### 2. Test Chat (AI)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me affordable laptops",
    "user_id": 1,
    "n_results": 5
  }'
```

### 3. Test Recommendations

```bash
curl "http://localhost:8000/recommend/user/1?n_recommendations=5"
```

### 4. Test Search

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "running shoes under $100",
    "user_id": 1,
    "n_results": 5
  }'
```

### 5. Open Web Interface

Navigate to:
- **Web UI**: http://localhost:8000/index.html
- **API Docs**: http://localhost:8000/docs
- **Interactive Testing**: http://localhost:8000/redoc

---

## Sample Data Reference

The system includes sample data for testing:

### Users (IDs 1-10)
All users have purchase history and can be used for recommendations.

### Products (15 items)
- **Electronics**: Wireless Headphones, Laptop Stand, Bluetooth Speaker, Phone Case
- **Sports**: Yoga Mat, Running Shoes, Water Bottle, Resistance Bands
- **Home**: Coffee Maker, Blender, Plant Pot, Cooking Pan
- **Health**: Protein Powder
- **Books**: Programming Book

### Try These Queries

```
"Show me affordable electronics"
"Find running shoes under $50"
"Recommend products like wireless headphones"
"I need yoga equipment"
"What are some premium tech gadgets?"
```

---

## What's Working?

| Feature | Without OpenAI | With OpenAI |
|---------|----------------|-------------|
| Product Search | ✅ Basic | ✅ AI-Powered |
| Recommendations | ✅ | ✅ |
| User Preferences | ✅ | ✅ |
| Conversation Memory | ✅ | ✅ |
| Natural Language Chat | ❌ | ✅ |
| Query Understanding | ❌ | ✅ |

**Without OpenAI:** System uses fallback logic for search and recommendations (still works!)

**With OpenAI:** Full natural language understanding and conversational AI

---

## Troubleshooting

### Docker Issues

**Containers won't start:**
```bash
docker-compose logs
docker-compose down -v
docker-compose up -d --build
```

**Port already in use:**
```bash
# Change ports in docker-compose.yml
# Or stop conflicting services
lsof -i :8000
```

### Local Development Issues

**Database connection refused:**
```bash
# Check if services are running
brew services list           # macOS
sudo systemctl status postgresql  # Linux

# Restart services
brew services restart postgresql@14
```

**"Database does not exist":**
```bash
createdb recommendation_db
python example.py
```

**"Module not found":**
```bash
pip install -r requirements.txt
```

**OpenAI errors:**
- Verify API key in `.env` file
- Check key at: https://platform.openai.com/api-keys
- Ensure key starts with `sk-`

### AWS Issues

**ECR push fails:**
```bash
# Re-authenticate
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

**ECS task fails:**
```bash
# Check logs
aws logs tail /ecs/recommendation-app --follow
```

**For detailed troubleshooting:** See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md)

---

## Next Steps

### 1. Explore the Features
- Try the chat interface
- Test recommendations
- View conversation history
- Check user preferences

### 2. Customize the System
- Add your own products
- Import real user data
- Customize the UI
- Adjust recommendation algorithms

### 3. Deploy to Production
- Set up AWS infrastructure
- Configure monitoring
- Set up CI/CD
- Enable HTTPS

### 4. Learn More
- **README.md** - Complete feature documentation
- **DOCKER_GUIDE.md** - Docker tips and tricks
- **AWS_DEPLOYMENT.md** - Production deployment guide
- **MEMORY_MANAGEMENT.md** - Memory system details

---

## Need Help?

### Check Service Status

**Docker:**
```bash
docker-compose ps
docker-compose logs -f app
```

**Local:**
```bash
# PostgreSQL
pg_isready

# MongoDB  
mongosh

# Redis
redis-cli ping

# API
curl http://localhost:8000/health
```

### Common Commands

```bash
# Docker
docker-compose up -d          # Start
docker-compose down           # Stop
docker-compose restart app    # Restart app
docker-compose logs -f app    # View logs

# Local
uvicorn main:app --reload     # Start server
python example.py             # Reset data
python test_chatbot.py        # Test features
```

### Documentation

- **API Reference**: http://localhost:8000/docs
- **System Architecture**: See README.md
- **Memory System**: See MEMORY_MANAGEMENT.md
- **AWS Deployment**: See AWS_DEPLOYMENT.md

---

**Ready to build amazing product recommendations! 🚀**
