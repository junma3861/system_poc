# Docker Quick Start

## 🐳 Running with Docker

### Option 1: Docker Compose (Recommended for Local Development)

Start all services (app + databases):

```bash
# Start services
docker-compose up -d

# Wait for databases to initialize (first run)
sleep 15

# Initialize database with sample data
docker-compose exec app python example.py

# View logs
docker-compose logs -f app

# Open in browser
open http://localhost:8000/docs
```

**Services started:**
- FastAPI app: http://localhost:8000
- PostgreSQL: localhost:5432
- MongoDB: localhost:27017
- Redis: localhost:6379

**Stop services:**
```bash
docker-compose down

# Remove volumes (deletes data)
docker-compose down -v
```

### Option 2: Docker Only (App Container)

Build and run just the app (requires external databases):

```bash
# Build image
docker build -t recommendation-system .

# Run container
docker run -d \
  --name recommendation-app \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e SQL_DATABASE_URL=postgresql://user:pass@host/db \
  -e MONGO_URI=mongodb://host:27017/ \
  -e REDIS_HOST=host \
  recommendation-system

# View logs
docker logs -f recommendation-app

# Stop container
docker stop recommendation-app
docker rm recommendation-app
```

## 🔧 Configuration

### Environment Variables

Create `.env.docker`:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Databases (use service names in docker-compose)
SQL_DATABASE_URL=postgresql://postgres:postgres@postgres:5432/recommendation_db
MONGO_URI=mongodb://mongodb:27017/
MONGO_DATABASE=recommendation_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Memory
SESSION_TTL=3600
MAX_CONTEXT_MESSAGES=10
```

Load environment file:
```bash
docker-compose --env-file .env.docker up -d
```

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me affordable laptops",
    "user_id": 1,
    "n_results": 5
  }'

# Test recommendations
curl http://localhost:8000/recommend/user/1?n_recommendations=5
```

## 📊 Monitoring

```bash
# View all logs
docker-compose logs -f

# View app logs only
docker-compose logs -f app

# View database logs
docker-compose logs -f postgres

# Container stats
docker stats
```

## 🛠️ Development with Docker

### Live Code Reload

Add volume mount for development:

```yaml
# docker-compose.override.yml
services:
  app:
    volumes:
      - .:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Then:
```bash
docker-compose up -d
# Code changes will auto-reload
```

### Execute Commands in Container

```bash
# Open shell
docker-compose exec app bash

# Run Python script
docker-compose exec app python script.py

# Initialize database
docker-compose exec app python example.py

# Run tests
docker-compose exec app python test_chatbot.py
```

### Access Databases

```bash
# PostgreSQL
docker-compose exec postgres psql -U postgres -d recommendation_db

# MongoDB
docker-compose exec mongodb mongosh recommendation_db

# Redis
docker-compose exec redis redis-cli
```

## 🚀 Production Build

### Multi-stage Build (Optimized)

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Build:
```bash
docker build -f Dockerfile.prod -t recommendation-system:prod .
```

### Resource Limits

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## 🔐 Security

### Non-root User

```dockerfile
# Add to Dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

### Scan Image

```bash
# Using Docker Scout
docker scout cves recommendation-system:latest

# Using Trivy
trivy image recommendation-system:latest
```

## 📦 Image Management

```bash
# List images
docker images

# Remove old images
docker image prune -a

# Tag for registry
docker tag recommendation-system:latest \
  your-registry/recommendation-system:v1.0

# Push to registry
docker push your-registry/recommendation-system:v1.0
```

## 🐛 Troubleshooting

### Container won't start?

```bash
# Check logs
docker-compose logs app

# Inspect container
docker inspect recommendation-app

# Check if ports are in use
lsof -i :8000
```

### Database connection issues?

```bash
# Test connectivity
docker-compose exec app pg_isready -h postgres -U postgres

# Check if databases are ready
docker-compose ps
```

### Out of memory?

```bash
# Increase memory limit
docker-compose up -d --scale app=1 --memory=4g
```

### Slow build?

```bash
# Use BuildKit
DOCKER_BUILDKIT=1 docker build -t recommendation-system .

# Clear build cache
docker builder prune
```

## 📚 Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart service
docker-compose restart app

# View logs
docker-compose logs -f

# Scale service
docker-compose up -d --scale app=3

# Update service
docker-compose up -d --build app

# Execute command
docker-compose exec app python script.py

# View running containers
docker ps

# View all containers
docker ps -a

# Remove all stopped containers
docker container prune

# Remove all unused volumes
docker volume prune
```

## 🎯 Quick Commands

```bash
# Full reset (removes all data)
docker-compose down -v && docker-compose up -d

# Rebuild and restart
docker-compose up -d --build

# View container IPs
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' container_name

# Copy file from container
docker cp recommendation-app:/app/logs/app.log ./logs/
```

---

**Ready to run? Start with: `docker-compose up -d`** 🐳
